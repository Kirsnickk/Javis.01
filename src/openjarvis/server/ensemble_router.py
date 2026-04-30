"""Ensemble inference router — query all models, synthesize one answer.

When the frontend enables Ensemble Mode the request hits
``POST /v1/chat/ensemble``.  The handler:

1. Fans the user prompt out to every requested model **in parallel**.
2. Collects each model's full response.
3. Builds a meta-prompt containing every model's answer.
4. Streams the **synthesizer** model's consolidated response back via SSE.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Sequence

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from openjarvis.core.types import Message, Role

logger = logging.getLogger(__name__)

ensemble_router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLOUD_PREFIXES = (
    "gpt-", "o1-", "o3-", "o4-", "chatgpt-",
    "claude-",
    "gemini-",
    "openrouter/",
    "MiniMax-",
    "deepseek-",
    "mistral-", "codestral-", "pixtral-", "ministral-",
    "grok-",
    "command-",
)


def _is_cloud(model: str) -> bool:
    from openjarvis.server.cloud_router import is_cloud_model
    return is_cloud_model(model)


def _to_messages(raw: list[dict[str, Any]]) -> list[Message]:
    msgs: list[Message] = []
    for m in raw:
        role_str = m.get("role", "user")
        role = Role(role_str) if role_str in {r.value for r in Role} else Role.USER
        msgs.append(Message(role=role, content=m.get("content", "")))
    return msgs


async def _generate_single_cloud(
    model: str,
    messages: Sequence[Message],
    temperature: float,
    max_tokens: int,
) -> str:
    """Collect the full response from a cloud model (non-streaming)."""
    from openjarvis.server.cloud_router import stream_cloud

    chunks: list[str] = []
    try:
        async for token in stream_cloud(model, messages, temperature, max_tokens):
            chunks.append(token)
    except Exception as exc:
        logger.warning("Ensemble: cloud model %s failed: %s", model, exc)
        return f"[Error: {exc}]"
    return "".join(chunks)


async def _generate_single_local(
    model: str,
    messages: Sequence[Message],
    temperature: float,
    max_tokens: int,
) -> str:
    """Collect the full response from a local Ollama model (non-streaming)."""
    from openjarvis.server.cloud_router import stream_local

    chunks: list[str] = []
    try:
        async for token in stream_local(model, messages, temperature, max_tokens):
            chunks.append(token)
    except Exception as exc:
        logger.warning("Ensemble: local model %s failed: %s", model, exc)
        return f"[Error: {exc}]"
    return "".join(chunks)


async def _generate_single(
    model: str,
    messages: Sequence[Message],
    temperature: float,
    max_tokens: int,
) -> tuple[str, str]:
    """Return (model_name, response_text)."""
    if _is_cloud(model):
        text = await _generate_single_cloud(model, messages, temperature, max_tokens)
    else:
        text = await _generate_single_local(model, messages, temperature, max_tokens)
    return model, text


def _build_synthesis_prompt(
    original_query: str,
    model_responses: list[tuple[str, str]],
) -> str:
    """Build the meta-prompt that the synthesizer model will receive."""
    parts = [
        "You are an expert AI synthesizer. Multiple AI models have answered the same question. "
        "Read ALL of their responses carefully, then produce the single best, most comprehensive, "
        "and accurate answer. Combine the best insights from each model. "
        "If models disagree, explain the different perspectives and give your best judgment.\n\n"
        f"## Original Question\n{original_query}\n\n"
        "## Model Responses\n"
    ]
    for i, (model_name, response) in enumerate(model_responses, 1):
        parts.append(f"### Model {i}: {model_name}\n{response}\n\n")

    parts.append(
        "## Your Task\n"
        "Synthesize all the above responses into one final, high-quality answer. "
        "Be thorough but concise. Use the best parts of each response."
    )
    return "".join(parts)


# ---------------------------------------------------------------------------
# SSE Endpoint
# ---------------------------------------------------------------------------


@ensemble_router.post("/v1/chat/ensemble")
async def ensemble_chat(request: Request):
    """Fan-out to multiple models, then synthesize a single answer."""
    body = await request.json()

    raw_messages = body.get("messages", [])
    models: list[str] = body.get("models", [])
    synthesizer: str = body.get("synthesizer", "")
    temperature: float = body.get("temperature", 0.7)
    max_tokens: int = body.get("max_tokens", 2048)

    if not models:
        return {"error": "No models specified for ensemble"}
    if not synthesizer:
        # Default: use the last model as synthesizer
        synthesizer = models[-1]

    messages = _to_messages(raw_messages)

    # Extract the user's original question (last user message)
    original_query = ""
    for m in reversed(messages):
        if m.role == Role.USER:
            original_query = m.content
            break

    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    async def generate():
        # ─── Phase 1: Report which models are thinking ──────────────
        phase_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "model": "ensemble",
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None,
            }],
            "ensemble_phase": "collecting",
            "ensemble_models": models,
        }
        yield f"data: {json.dumps(phase_chunk)}\n\n"

        # ─── Phase 2: Fan-out to all models in parallel ─────────────
        tasks = [
            _generate_single(model, messages, temperature, max_tokens)
            for model in models
        ]

        model_responses: list[tuple[str, str]] = []
        completed = 0

        # Use asyncio.as_completed so we can stream progress updates
        for coro in asyncio.as_completed(tasks):
            model_name, response_text = await coro
            model_responses.append((model_name, response_text))
            completed += 1

            # Send progress update
            progress_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "model": "ensemble",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": None,
                }],
                "ensemble_phase": "model_done",
                "ensemble_model": model_name,
                "ensemble_progress": f"{completed}/{len(models)}",
            }
            yield f"data: {json.dumps(progress_chunk)}\n\n"

        # ─── Phase 3: Synthesize ────────────────────────────────────
        synth_phase = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "model": "ensemble",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": None,
            }],
            "ensemble_phase": "synthesizing",
            "ensemble_synthesizer": synthesizer,
            "ensemble_responses": [
                {"model": name, "response": text}
                for name, text in model_responses
            ],
        }
        yield f"data: {json.dumps(synth_phase)}\n\n"

        # Build synthesis prompt
        synthesis_prompt = _build_synthesis_prompt(original_query, model_responses)
        synth_messages = [Message(role=Role.USER, content=synthesis_prompt)]

        # Stream synthesizer response
        try:
            if _is_cloud(synthesizer):
                from openjarvis.server.cloud_router import stream_cloud
                token_iter = stream_cloud(
                    synthesizer, synth_messages, temperature, max_tokens
                )
            else:
                from openjarvis.server.cloud_router import stream_local
                token_iter = stream_local(
                    synthesizer, synth_messages, temperature, max_tokens
                )

            async for token in token_iter:
                content_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "model": synthesizer,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None,
                    }],
                }
                yield f"data: {json.dumps(content_chunk)}\n\n"

        except Exception as exc:
            logger.error("Ensemble synthesizer error: %s", exc, exc_info=True)
            err_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "model": synthesizer,
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"\n\nError during synthesis: {exc}"},
                    "finish_reason": "stop",
                }],
            }
            yield f"data: {json.dumps(err_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            return

        # Finish
        finish_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "model": synthesizer,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }],
            "ensemble_phase": "done",
        }
        yield f"data: {json.dumps(finish_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


__all__ = ["ensemble_router"]
