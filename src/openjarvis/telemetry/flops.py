"""FLOPs estimation and Model FLOPs Utilization (MFU) computation."""

from __future__ import annotations

GPU_PEAK_TFLOPS_BF16: dict[str, float] = {
    "H100": 989.0,
    "H200": 989.0,
    "A100": 312.0,
    "A10G": 31.2,
    "L4": 30.3,
    "L40": 181.0,
    "L40S": 362.0,
    "T4": 65.1,
    "V100": 125.0,
    "4090": 82.6,
    "4080": 48.7,
    "3090": 35.6,
    "M3 Max": 14.2,
    "M3 Ultra": 27.0,
    "M4 Max": 18.0,
}

MODEL_PARAMS_B: dict[str, float] = {
    # Qwen
    "qwen3:8b": 8.0,
    "qwen3:0.6b": 0.6,
    "qwen3:4b": 4.0,
    "qwen3.5:0.8b": 0.8,
    "qwen3.5:2b": 2.0,
    "qwen3.5:4b": 4.0,
    "qwen3.5:9b": 9.0,
    "qwen3.5:27b": 27.0,
    "qwen3.5:35b": 35.0,
    "qwen3.5:122b": 122.0,
    # Llama
    "llama-3.1-70b": 70.0,
    "llama-3.1-8b": 8.0,
    "llama3.3": 8.0,
    "llama3.1:70b": 70.0,
    # Mistral / Mixtral
    "mistral-7b": 7.0,
    "mistral": 7.0,
    "mixtral-8x7b": 47.0,
    "mixtral": 47.0,
    "mistral-nemo": 12.0,
    # Gemma
    "gemma3": 4.0,
    "gemma3:12b": 12.0,
    "gemma3:27b": 27.0,
    # DeepSeek
    "deepseek-r1:7b": 7.0,
    "deepseek-r1:14b": 14.0,
    "deepseek-r1:32b": 32.0,
    "deepseek-coder-v2": 16.0,
    # Phi
    "phi4": 14.0,
    "phi3:mini": 3.8,
    "phi3:medium": 14.0,
    # Code
    "codellama": 7.0,
    "codellama:34b": 34.0,
    "starcoder2": 7.0,
    # Cloud (approximate)
    "gpt-4o": 200.0,
    "gpt-4o-mini": 8.0,
    "claude-sonnet-4": 70.0,
    "claude-opus-4": 175.0,
    "gemini-2.5-pro": 175.0,
    "deepseek-chat": 236.0,
    "mistral-large": 123.0,
    "grok-3": 314.0,
    "command-r-plus": 104.0,
}


def _get_params_b(model: str) -> float:
    """Look up model parameter count (billions)."""
    params_b = MODEL_PARAMS_B.get(model, 0.0)
    if params_b == 0.0:
        for key, val in MODEL_PARAMS_B.items():
            if model.startswith(key.split(":")[0]):
                params_b = val
                break
    return params_b


def estimate_flops(
    model: str, input_tokens: int, output_tokens: int
) -> tuple[float, float]:
    """Estimate FLOPs for an inference pass (assumes KV caching).

    Uses the 2 * P * T approximation where P = params, T = total tokens.
    Returns (total_flops, flops_per_token).

    ``input_tokens`` must include system-prompt tokens and must *not*
    be reduced for KV-cache reuse — it should represent the full prompt
    size that was sent to the engine.
    """
    params_b = _get_params_b(model)
    total_tokens = input_tokens + output_tokens
    params = params_b * 1e9
    total_flops = 2.0 * params * total_tokens
    flops_per_token = 2.0 * params if total_tokens > 0 else 0.0
    return (total_flops, flops_per_token)


def estimate_flops_no_kv_cache(
    model: str, input_tokens: int, output_tokens: int
) -> tuple[float, float]:
    """Estimate FLOPs without KV caching (full recompute per token).

    Without KV cache, each token is re-processed for every subsequent token.
    FLOPs = P * N * (N + 1) where P = params, N = total_tokens.
    Returns (total_flops, flops_per_token_avg).
    """
    params_b = _get_params_b(model)
    total_tokens = input_tokens + output_tokens
    if total_tokens == 0:
        return (0.0, 0.0)
    params = params_b * 1e9
    total_flops = params * total_tokens * (total_tokens + 1)
    flops_per_token = total_flops / total_tokens
    return (total_flops, flops_per_token)


def compute_mfu(
    flops: float, duration_s: float, gpu_name: str, num_gpus: int = 1
) -> float:
    """Compute Model FLOPs Utilization.

    MFU = actual_tflops / (peak_tflops * num_gpus)
    """
    peak = GPU_PEAK_TFLOPS_BF16.get(gpu_name, 0.0)
    if peak == 0.0:
        # Try substring matching
        for key, val in GPU_PEAK_TFLOPS_BF16.items():
            if key.lower() in gpu_name.lower():
                peak = val
                break
    if peak <= 0 or duration_s <= 0:
        return 0.0
    actual_tflops = flops / (duration_s * 1e12)
    return (actual_tflops / (peak * num_gpus)) * 100.0
