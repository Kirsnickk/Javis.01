# Kế Hoạch Triển Khai AI Agent Kiểu Jarvis

> Dựa trên OpenJarvis · Local-first + Cloud fallback · Tất cả tính năng

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Yêu cầu hệ thống](#2-yêu-cầu-hệ-thống)
3. [Giai đoạn 1 — Cài đặt nền tảng](#giai-đoạn-1--cài-đặt-nền-tảng)
4. [Giai đoạn 2 — Cấu hình Engine (Local + Cloud)](#giai-đoạn-2--cấu-hình-engine-local--cloud)
5. [Giai đoạn 3 — Kích hoạt tính năng Trợ lý hỏi đáp](#giai-đoạn-3--kích-hoạt-tính-năng-trợ-lý-hỏi-đáp)
6. [Giai đoạn 4 — Tính năng Automation (Email + Lịch)](#giai-đoạn-4--tính-năng-automation-email--lịch)
7. [Giai đoạn 5 — Nghiên cứu & Tìm kiếm tài liệu](#giai-đoạn-5--nghiên-cứu--tìm-kiếm-tài-liệu)
8. [Giai đoạn 6 — Tính năng Lập trình & Code](#giai-đoạn-6--tính-năng-lập-trình--code)
9. [Giai đoạn 7 — Memory & Skills](#giai-đoạn-7--memory--skills)
10. [Giai đoạn 8 — Custom Agent & Tools](#giai-đoạn-8--custom-agent--tools)
11. [Giai đoạn 9 — Frontend & Giao diện](#giai-đoạn-9--frontend--giao-diện)
12. [Giai đoạn 10 — Deploy & Production](#giai-đoạn-10--deploy--production)
13. [Cấu trúc thư mục dự án](#cấu-trúc-thư-mục-dự-án)
14. [Kiểm thử & Debug](#kiểm-thử--debug)
15. [Lộ trình & Timeline](#lộ-trình--timeline)

---

## 1. Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────┐
│                    Jarvis Agent                     │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Chat UI │  │ REST API │  │  CLI (jarvis ask) │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       └─────────────┴─────────────────┘             │
│                      │                              │
│              ┌───────▼────────┐                     │
│              │  Orchestrator  │                     │
│              │    Agent       │                     │
│              └───────┬────────┘                     │
│         ┌────────────┼────────────┐                 │
│    ┌────▼───┐  ┌─────▼────┐  ┌───▼─────┐           │
│    │ Skills │  │  Memory  │  │  Tools  │           │
│    └────────┘  └──────────┘  └─────────┘           │
│                      │                              │
│         ┌────────────┼────────────┐                 │
│   ┌─────▼──┐   ┌─────▼──┐  ┌─────▼──┐              │
│   │ Ollama │   │ Claude │  │ OpenAI │              │
│   │(local) │   │  API   │  │  API   │              │
│   └────────┘   └────────┘  └────────┘              │
└─────────────────────────────────────────────────────┘
```

**Nguyên tắc hoạt động:**
- Local model (Ollama) xử lý 80-90% yêu cầu thông thường
- Cloud API (Claude) được gọi khi local model không đủ mạnh hoặc gặp lỗi
- Toàn bộ dữ liệu cá nhân lưu trên máy, không gửi lên cloud trừ khi cần thiết

---

## 2. Yêu cầu hệ thống

### Phần cứng tối thiểu

| Thành phần | Tối thiểu | Khuyến nghị |
|------------|-----------|-------------|
| RAM | 8 GB | 16 GB+ |
| CPU | 4 nhân | 8 nhân+ |
| Ổ cứng | 20 GB trống | 50 GB+ SSD |
| GPU | Không bắt buộc | NVIDIA 8GB VRAM+ |

### Phần mềm cần cài

| Tool | Phiên bản | Mục đích |
|------|-----------|----------|
| Python | 3.10+ | Runtime chính |
| uv | mới nhất | Package manager |
| Rust | stable | Build extension |
| Git | mới nhất | Clone repo |
| Ollama | mới nhất | Chạy model local |
| Node.js | 18+ | Frontend (nếu cần) |

### OS được hỗ trợ

- **Linux**: Ubuntu 20.04+, Debian 11+ (khuyến nghị)
- **macOS**: 12 Monterey+ (có hướng dẫn riêng)
- **Windows**: Dùng WSL2 + Ubuntu

---

## Giai đoạn 1 — Cài đặt nền tảng

### Bước 1.1 — Cài Python 3.10+

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip build-essential
python3 --version  # Kiểm tra: Python 3.10.x
```

**macOS:**
```bash
brew install python@3.12
python3 --version
```

### Bước 1.2 — Cài uv (package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # hoặc source ~/.zshrc
uv --version      # Kiểm tra
```

### Bước 1.3 — Cài Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
rustc --version   # Kiểm tra: rustc 1.x.x
cargo --version
```

### Bước 1.4 — Clone và cài OpenJarvis

```bash
# Clone repo
git clone https://github.com/open-jarvis/OpenJarvis.git
cd OpenJarvis

# Cài core framework
uv sync

# Cài thêm server (FastAPI)
uv sync --extra server

# Cài thêm dev tools (nếu muốn contribute)
uv sync --extra dev

# Build Rust extension (bắt buộc)
uv run maturin develop -m rust/crates/openjarvis-python/Cargo.toml

# Nếu dùng Python 3.14+, thêm biến môi trường trước:
# export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
```

### Bước 1.5 — Cài Ollama (local inference)

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Khởi động Ollama service
ollama serve &

# Pull model (chọn 1 trong các options):
ollama pull qwen3:8b        # Nhẹ, nhanh (~5GB, RAM 8GB)
ollama pull llama3.2:8b     # Cân bằng (~5GB)
ollama pull mistral:7b      # Tốt cho code (~4GB)
# ollama pull llama3.1:70b  # Mạnh nhất, cần RAM 48GB+

# Kiểm tra model đã pull
ollama list
```

### Bước 1.6 — Khởi tạo Jarvis

```bash
# Auto-detect hardware và cấu hình tối ưu
uv run jarvis init

# Kiểm tra tất cả thành phần
uv run jarvis doctor
```

**Output mong đợi của `jarvis doctor`:**
```
✓ Python 3.12.x
✓ uv installed
✓ Rust extension compiled
✓ Ollama running (qwen3:8b available)
✓ Config file found
```

---

## Giai đoạn 2 — Cấu hình Engine (Local + Cloud)

### Bước 2.1 — Cấu hình Local Engine (Ollama)

Tạo/chỉnh sửa file `configs/openjarvis/engine.yaml`:

```yaml
# configs/openjarvis/engine.yaml
engine:
  primary: ollama
  fallback: anthropic

ollama:
  base_url: http://localhost:11434
  model: qwen3:8b
  timeout: 30
  max_retries: 2

fallback:
  trigger_on:
    - model_not_found
    - timeout
    - context_too_long
  max_tokens_local: 8192
```

### Bước 2.2 — Cấu hình Cloud Fallback (Claude API)

```bash
# Thêm API keys vào biến môi trường
# Tạo file .env trong thư mục gốc

cat > .env << 'EOF'
# Claude (Anthropic) - primary cloud fallback
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# OpenAI - secondary fallback (tùy chọn)
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# Google Gemini (tùy chọn)
GOOGLE_API_KEY=xxxxxxxxxxxx
EOF

# Load biến môi trường
source .env
# Hoặc thêm vào ~/.bashrc để tự động load
echo 'source ~/OpenJarvis/.env' >> ~/.bashrc
```

### Bước 2.3 — Test fallback hoạt động

```bash
# Test local engine
uv run jarvis ask "xin chào"

# Test cloud fallback (tắt Ollama trước)
ollama stop
uv run jarvis ask "xin chào"
# Lần này sẽ dùng Claude API

# Bật lại Ollama
ollama serve &
```

### Bước 2.4 — Cấu hình routing thông minh

Chỉnh `configs/openjarvis/routing.yaml`:

```yaml
# Gửi sang cloud khi query phức tạp
routing:
  complexity_threshold: 0.7   # 0-1, cao hơn = ít gọi cloud hơn
  max_local_tokens: 4096
  
  # Loại query luôn dùng local
  always_local:
    - simple_chat
    - file_operations
    - calendar_read
  
  # Loại query luôn dùng cloud
  always_cloud:
    - complex_reasoning
    - code_review
    - long_document_analysis
```

---

## Giai đoạn 3 — Kích hoạt tính năng Trợ lý hỏi đáp

### Bước 3.1 — Preset chat đơn giản

```bash
jarvis init --preset chat-simple

# Test
uv run jarvis ask "Thủ đô của Việt Nam là gì?"
uv run jarvis ask "Giải thích quantum computing bằng tiếng Việt"
```

### Bước 3.2 — Chế độ hội thoại nhiều lượt

```bash
# Chế độ interactive (giống ChatGPT)
uv run jarvis chat

# Trong chat session:
# > xin chào Jarvis
# > nhớ tên tôi là Minh
# > tên tôi là gì?  ← Jarvis sẽ nhớ
```

### Bước 3.3 — Cấu hình nhân cách Jarvis

Tạo file `configs/openjarvis/persona.yaml`:

```yaml
persona:
  name: Jarvis
  language: vi  # Tiếng Việt mặc định
  tone: professional_friendly
  
  system_prompt: |
    Bạn là Jarvis, trợ lý AI cá nhân thông minh.
    Trả lời bằng tiếng Việt trừ khi được yêu cầu khác.
    Ngắn gọn, chính xác, thực tế.
    Luôn hỏi thêm khi câu hỏi không rõ ràng.
  
  capabilities:
    - Trả lời câu hỏi
    - Phân tích thông tin
    - Viết và chỉnh sửa văn bản
    - Giải thích khái niệm phức tạp
```

### Bước 3.4 — Thêm giọng nói (TTS/STT, tuỳ chọn)

```bash
# Cài thêm dependencies cho voice
pip install openai-whisper pyttsx3

# Kích hoạt voice mode
uv run jarvis ask --voice "Jarvis, hôm nay thời tiết thế nào?"
```

---

## Giai đoạn 4 — Tính năng Automation (Email + Lịch)

### Bước 4.1 — Preset morning digest

```bash
jarvis init --preset morning-digest-minimal
```

### Bước 4.2 — Kết nối Google (Gmail + Calendar + Tasks)

```bash
# Một lần OAuth duy nhất cho cả Gmail, Calendar, Tasks
jarvis connect gdrive

# Trình duyệt sẽ mở → Đăng nhập Google → Cấp quyền
# Token được lưu local tại ~/.jarvis/credentials/google.json
```

**Cấu hình quyền truy cập** (`configs/openjarvis/google.yaml`):
```yaml
google:
  scopes:
    - https://www.googleapis.com/auth/gmail.readonly
    - https://www.googleapis.com/auth/calendar.readonly
    - https://www.googleapis.com/auth/tasks.readonly
  
  gmail:
    max_emails: 20
    folders: [INBOX, STARRED]
    exclude_promotions: true
  
  calendar:
    days_ahead: 7
    include_reminders: true
```

### Bước 4.3 — Chạy morning digest đầu tiên

```bash
# Tạo briefing buổi sáng
uv run jarvis digest --fresh

# Output sẽ bao gồm:
# - Tóm tắt email quan trọng hôm nay
# - Lịch họp sắp tới
# - Tasks còn pending
# - Tin tức (nếu cấu hình)
```

### Bước 4.4 — Lên lịch tự động mỗi sáng

```bash
# Thêm vào crontab (chạy 7:00 sáng mỗi ngày)
crontab -e

# Thêm dòng:
0 7 * * * cd /path/to/OpenJarvis && uv run jarvis digest --fresh >> ~/.jarvis/logs/digest.log 2>&1
```

### Bước 4.5 — Agent giám sát liên tục

```bash
# Khởi động monitor agent (chạy nền, kiểm tra email/lịch định kỳ)
jarvis init --preset scheduled-monitor

# Cấu hình tần suất kiểm tra
# configs/openjarvis/monitor.yaml:
# check_interval: 900  # 15 phút
# notify_on: [meeting_reminder, urgent_email, task_deadline]
```

---

## Giai đoạn 5 — Nghiên cứu & Tìm kiếm tài liệu

### Bước 5.1 — Preset deep research

```bash
jarvis init --preset deep-research
```

### Bước 5.2 — Index tài liệu cá nhân (RAG)

```bash
# Index thư mục tài liệu (PDF, DOCX, TXT, MD...)
uv run jarvis memory index ./docs/
uv run jarvis memory index ~/Downloads/papers/
uv run jarvis memory index ~/Notes/

# Kiểm tra số lượng tài liệu đã index
uv run jarvis memory status
```

**Cấu hình RAG** (`configs/openjarvis/memory.yaml`):
```yaml
memory:
  backend: local  # Lưu local, không gửi lên cloud
  embedding_model: nomic-embed-text  # Chạy qua Ollama
  chunk_size: 512
  chunk_overlap: 64
  
  index_paths:
    - ~/docs
    - ~/Notes
    - ~/Downloads/papers
  
  file_types: [pdf, docx, txt, md, html]
```

### Bước 5.3 — Pull embedding model

```bash
ollama pull nomic-embed-text
# Model này chuyên dùng để tạo embeddings, nhẹ (~274MB)
```

### Bước 5.4 — Truy vấn tài liệu

```bash
# Hỏi về nội dung tài liệu đã index
uv run jarvis ask "Tóm tắt tất cả emails về Project X"
uv run jarvis ask "Tìm tất cả tài liệu về machine learning"
uv run jarvis ask "Báo cáo Q3 nói gì về doanh thu?"

# Research đa nguồn (kết hợp web + tài liệu local)
uv run jarvis ask --research "Xu hướng AI năm 2025 và tác động đến công việc của tôi"
```

### Bước 5.5 — Cài skill nghiên cứu

```bash
# Skill tìm kiếm arXiv (paper khoa học)
uv run jarvis skill install hermes:arxiv

# Sync tất cả skill về nghiên cứu
uv run jarvis skill sync hermes --category research

# Sử dụng
uv run jarvis ask "Dùng arxiv skill tìm papers về RAG năm 2024"
```

---

## Giai đoạn 6 — Tính năng Lập trình & Code

### Bước 6.1 — Preset code assistant

```bash
jarvis init --preset code-assistant
```

### Bước 6.2 — Cài model tốt cho code

```bash
# Model chuyên code (chọn 1)
ollama pull qwen2.5-coder:7b    # Tốt cho code, nhẹ
ollama pull deepseek-coder:6.7b # Mạnh về code

# Cấu hình dùng model code cho queries liên quan code
# configs/openjarvis/routing.yaml:
# code_model: qwen2.5-coder:7b
```

### Bước 6.3 — Agent viết và chạy code (CodeAct)

```bash
# Agent native_openhands: tự sinh code Python rồi chạy
uv run jarvis run --agent native_openhands \
  "Viết script Python đọc file CSV và tạo báo cáo thống kê"

# Agent có quyền:
# - Viết file
# - Chạy Python code
# - Đọc output
# - Sửa code nếu có lỗi (tự động)
```

### Bước 6.4 — Review code

```bash
# Review file code hiện có
uv run jarvis ask "Review file này và tìm bugs: $(cat myapp.py)"

# Hoặc dùng file path
uv run jarvis review ./src/main.py

# Review toàn bộ project
uv run jarvis review ./src/ --summary
```

### Bước 6.5 — Tích hợp với IDE (VS Code)

```bash
# Cài extension (nếu muốn dùng trong VS Code)
# Hoặc dùng qua terminal trong terminal tích hợp của VS Code

# Alias tiện lợi thêm vào ~/.bashrc
echo 'alias j="uv run jarvis ask"' >> ~/.bashrc
echo 'alias jcode="uv run jarvis run --agent native_openhands"' >> ~/.bashrc
source ~/.bashrc

# Dùng nhanh:
j "Giải thích hàm này"
jcode "Tạo REST API với FastAPI"
```

---

## Giai đoạn 7 — Memory & Skills

### Bước 7.1 — Bật persistent memory

```bash
# Jarvis nhớ thông tin giữa các session
# configs/openjarvis/memory.yaml:
# persistent: true
# user_profile: ~/.jarvis/profile.json

# Lần đầu giới thiệu bản thân
uv run jarvis ask "Tên tôi là Minh, tôi là backend developer, thích Python"

# Lần sau Jarvis sẽ nhớ
uv run jarvis ask "Gợi ý framework phù hợp cho tôi"
# → Jarvis biết bạn thích Python
```

### Bước 7.2 — Cài đặt Skills từ cộng đồng

```bash
# Import từ Hermes Agent (~150 skills chất lượng cao)
uv run jarvis skill install hermes:arxiv          # Tìm kiếm paper
uv run jarvis skill install hermes:code-explainer # Giải thích code
uv run jarvis skill install hermes:summarizer     # Tóm tắt tài liệu

# Import từ OpenClaw (~13,700 community skills)
uv run jarvis skill sync hermes --category research
uv run jarvis skill sync hermes --category productivity
uv run jarvis skill sync hermes --category coding
```

### Bước 7.3 — Tạo custom skill

Tạo file `skills/my_skills/daily_report.py`:

```python
"""
Skill: daily_report
Description: Tạo báo cáo công việc hàng ngày tự động
"""

def daily_report(agent, date: str = "today") -> str:
    """Tổng hợp công việc trong ngày và tạo báo cáo"""
    
    # Lấy emails đã xử lý
    emails = agent.tools.gmail.get_processed_today()
    
    # Lấy tasks đã hoàn thành
    tasks = agent.tools.tasks.get_completed(date=date)
    
    # Lấy lịch họp
    meetings = agent.tools.calendar.get_events(date=date)
    
    # Tổng hợp bằng LLM
    summary = agent.llm.complete(f"""
    Tạo báo cáo công việc ngày {date}:
    Emails: {emails}
    Tasks hoàn thành: {tasks}
    Cuộc họp: {meetings}
    """)
    
    return summary
```

```bash
# Đăng ký skill
uv run jarvis skill register ./skills/my_skills/daily_report.py

# Sử dụng
uv run jarvis ask "Dùng daily_report skill để tạo báo cáo hôm nay"
```

### Bước 7.4 — Optimize skills từ lịch sử

```bash
# Phân tích trace history và tối ưu skills
uv run jarvis optimize skills --policy dspy

# Benchmark kết quả
uv run jarvis bench skills --max-samples 20 --seeds 42
```

---

## Giai đoạn 8 — Custom Agent & Tools

### Bước 8.1 — Tạo Custom Agent

Tạo file `src/openjarvis/agents/my_agent.py`:

```python
from openjarvis.core.agent import BaseAgent
from openjarvis.core.tools import ToolRegistry

class MyPersonalAgent(BaseAgent):
    """Agent cá nhân với tính năng tùy chỉnh"""
    
    name = "my_personal_agent"
    description = "Agent cá nhân của tôi"
    
    def __init__(self, config):
        super().__init__(config)
        self.tools = ToolRegistry([
            "gmail",
            "calendar", 
            "web_search",
            "code_executor",
            "file_manager",
        ])
    
    async def run(self, query: str, context: dict = None) -> str:
        # Phân tích intent
        intent = await self.classify_intent(query)
        
        # Routing dựa trên intent
        if intent == "research":
            return await self.research_workflow(query)
        elif intent == "automation":
            return await self.automation_workflow(query)
        elif intent == "coding":
            return await self.coding_workflow(query)
        else:
            return await self.chat_workflow(query)
    
    async def research_workflow(self, query: str) -> str:
        # Search web + tài liệu local + synthesize
        web_results = await self.tools.web_search.search(query)
        local_docs = await self.memory.search(query, k=5)
        
        return await self.llm.synthesize(
            query=query,
            sources=[web_results, local_docs]
        )
    
    async def coding_workflow(self, query: str) -> str:
        # Dùng model code chuyên biệt
        return await self.llm.complete(
            query,
            model="qwen2.5-coder:7b",
            system="Bạn là expert programmer. Trả lời bằng code có comments tiếng Việt."
        )
```

### Bước 8.2 — Đăng ký Agent

Thêm vào `configs/openjarvis/agents.yaml`:

```yaml
agents:
  default: my_personal_agent
  
  my_personal_agent:
    class: openjarvis.agents.my_agent.MyPersonalAgent
    config:
      max_steps: 10
      verbose: true
      fallback_agent: orchestrator
```

### Bước 8.3 — Tạo Custom Tool

Tạo file `src/openjarvis/tools/my_tools.py`:

```python
from openjarvis.core.tool import BaseTool

class WeatherTool(BaseTool):
    """Tool lấy thông tin thời tiết"""
    
    name = "weather"
    description = "Lấy thông tin thời tiết hiện tại và dự báo"
    
    async def get_current(self, city: str) -> dict:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://wttr.in/{city}?format=j1"
            )
            data = resp.json()
            return {
                "city": city,
                "temp_c": data["current_condition"][0]["temp_C"],
                "desc": data["current_condition"][0]["weatherDesc"][0]["value"],
                "humidity": data["current_condition"][0]["humidity"],
            }


class NotionTool(BaseTool):
    """Tool tích hợp Notion"""
    
    name = "notion"
    description = "Đọc và ghi Notion pages/databases"
    
    def __init__(self, api_key: str):
        from notion_client import Client
        self.client = Client(auth=api_key)
    
    async def search(self, query: str) -> list:
        results = self.client.search(query=query)
        return results["results"]
    
    async def create_page(self, title: str, content: str, parent_id: str) -> str:
        page = self.client.pages.create(
            parent={"page_id": parent_id},
            properties={"title": [{"text": {"content": title}}]},
            children=[{"paragraph": {"rich_text": [{"text": {"content": content}}]}}]
        )
        return page["id"]
```

### Bước 8.4 — Đăng ký Tool

```bash
# Thêm vào tool registry
# configs/openjarvis/tools.yaml:

# tools:
#   weather:
#     class: openjarvis.tools.my_tools.WeatherTool
#   notion:
#     class: openjarvis.tools.my_tools.NotionTool
#     config:
#       api_key: ${NOTION_API_KEY}

# Test tool
uv run jarvis ask "Thời tiết TP.HCM hôm nay thế nào?"
```

---

## Giai đoạn 9 — Frontend & Giao diện

### Bước 9.1 — Khởi động web server

```bash
# Khởi động FastAPI server
uv run jarvis server --port 8000

# Truy cập tại: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Bước 9.2 — Build frontend

```bash
cd frontend
npm install
npm run dev    # Development
npm run build  # Production
```

### Bước 9.3 — Tùy biến giao diện

Chỉnh sửa `frontend/src/components/ChatInterface.tsx`:

```typescript
// Thêm tính năng gợi ý nhanh (quick actions)
const QUICK_ACTIONS = [
  { label: "Briefing sáng", prompt: "Tóm tắt email và lịch hôm nay" },
  { label: "Nghiên cứu", prompt: "Nghiên cứu về..." },
  { label: "Viết code", prompt: "Viết code Python để..." },
  { label: "Báo cáo ngày", prompt: "Tạo báo cáo công việc hôm nay" },
];
```

### Bước 9.4 — Desktop App (Electron, tùy chọn)

```bash
# Dùng bản desktop đã có sẵn
# Download từ: https://github.com/open-jarvis/OpenJarvis/releases

# Hoặc build từ source:
cd frontend
npm install electron electron-builder
npm run build:desktop
```

---

## Giai đoạn 10 — Deploy & Production

### Bước 10.1 — Deploy với Docker

Tạo file `docker-compose.yml`:

```yaml
version: '3.8'

services:
  jarvis:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ~/.jarvis:/root/.jarvis  # Giữ memory + credentials
      - ./configs:/app/configs
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    # Nếu có GPU NVIDIA:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - capabilities: [gpu]

volumes:
  ollama_data:
```

```bash
# Build và chạy
docker-compose up -d

# Pull model vào container Ollama
docker exec jarvis-ollama-1 ollama pull qwen3:8b

# Kiểm tra logs
docker-compose logs -f jarvis
```

### Bước 10.2 — Deploy lên server (VPS/cloud)

```bash
# Trên server Ubuntu
git clone https://github.com/open-jarvis/OpenJarvis.git
cd OpenJarvis

# Dùng Docker
docker-compose up -d

# Hoặc cài trực tiếp + systemd service
sudo nano /etc/systemd/system/jarvis.service
```

Nội dung file `jarvis.service`:

```ini
[Unit]
Description=Jarvis AI Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/OpenJarvis
Environment=ANTHROPIC_API_KEY=sk-ant-xxx
ExecStart=/home/ubuntu/.local/bin/uv run jarvis server --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable jarvis
sudo systemctl start jarvis
sudo systemctl status jarvis
```

### Bước 10.3 — HTTPS với Nginx + SSL

```bash
# Cài Nginx và Certbot
sudo apt install nginx certbot python3-certbot-nginx

# Cấu hình Nginx reverse proxy
sudo nano /etc/nginx/sites-available/jarvis
```

```nginx
server {
    server_name jarvis.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/
sudo certbot --nginx -d jarvis.yourdomain.com
sudo systemctl reload nginx
```

### Bước 10.4 — Monitoring & Logging

```bash
# Xem logs realtime
uv run jarvis logs --follow

# Xem performance metrics
uv run jarvis stats

# Backup memory và credentials
uv run jarvis backup --output ~/jarvis-backup-$(date +%Y%m%d).tar.gz
```

---

## Cấu trúc thư mục dự án

```
OpenJarvis/
├── configs/
│   └── openjarvis/
│       ├── engine.yaml         ← Cấu hình local/cloud engine
│       ├── routing.yaml        ← Logic routing queries
│       ├── memory.yaml         ← RAG và persistent memory
│       ├── persona.yaml        ← Nhân cách Jarvis
│       ├── agents.yaml         ← Đăng ký agents
│       ├── tools.yaml          ← Đăng ký tools
│       ├── google.yaml         ← Gmail/Calendar config
│       └── monitor.yaml        ← Scheduled monitor config
│
├── src/openjarvis/
│   ├── agents/
│   │   ├── my_agent.py         ← Custom agent của bạn
│   │   ├── morning_digest.py
│   │   ├── deep_research.py
│   │   └── ...
│   ├── tools/
│   │   ├── my_tools.py         ← Custom tools
│   │   ├── weather.py
│   │   └── ...
│   └── skills/
│       └── my_skills/
│           └── daily_report.py
│
├── frontend/                   ← TypeScript/React UI
├── rust/                       ← Rust extension (performance)
├── .env                        ← API keys (KHÔNG commit lên git)
├── .gitignore                  ← Phải include .env
└── docker-compose.yml
```

---

## Kiểm thử & Debug

### Chạy test suite

```bash
uv run pytest tests/ -v

# Test chỉ một module
uv run pytest tests/test_agents.py -v

# Test với coverage
uv run pytest tests/ --cov=openjarvis --cov-report=html
```

### Debug commands hữu ích

```bash
# Xem version và thông tin
uv run jarvis --version
uv run jarvis info

# Chẩn đoán vấn đề
uv run jarvis doctor --verbose

# Xem cấu hình hiện tại
uv run jarvis config show

# Reset về mặc định
uv run jarvis config reset

# Xem lịch sử queries
uv run jarvis history --last 20

# Benchmark hiệu năng
uv run jarvis bench --preset chat-simple --samples 10
```

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `Ollama connection refused` | Ollama chưa chạy | `ollama serve &` |
| `Model not found` | Chưa pull model | `ollama pull qwen3:8b` |
| `API key invalid` | Key sai hoặc hết hạn | Kiểm tra `.env` |
| `Rust extension not found` | Chưa build | `uv run maturin develop ...` |
| `Memory index empty` | Chưa index | `jarvis memory index ./docs/` |
| `Permission denied` | Thiếu quyền file | `chmod +x scripts/*.sh` |

---

## Lộ trình & Timeline

### Tuần 1 — Nền tảng

- [x] Giai đoạn 1: Cài đặt hoàn tất
- [x] Giai đoạn 2: Engine local + cloud hoạt động
- [x] Giai đoạn 3: Trợ lý hỏi đáp cơ bản

### Tuần 2 — Tính năng chính

- [ ] Giai đoạn 4: Automation email + lịch
- [ ] Giai đoạn 5: RAG + tìm kiếm tài liệu
- [ ] Giai đoạn 6: Code assistant

### Tuần 3 — Tùy biến

- [ ] Giai đoạn 7: Memory + Skills
- [ ] Giai đoạn 8: Custom agent + tools
- [ ] Giai đoạn 9: Frontend

### Tuần 4 — Production

- [ ] Giai đoạn 10: Deploy Docker + server
- [ ] Monitoring + backup
- [ ] Tối ưu hiệu năng

---

> **Ghi chú bảo mật:**
> - Không bao giờ commit file `.env` lên Git
> - Credentials Google OAuth lưu local tại `~/.jarvis/credentials/`
> - API keys cloud chỉ dùng khi local model không đủ
> - Dữ liệu cá nhân (email, lịch) không gửi lên cloud trừ khi bạn cho phép

---

*Tài liệu: OpenJarvis Implementation Plan v1.0*
*Repo: https://github.com/open-jarvis/OpenJarvis*
*Docs: https://open-jarvis.github.io/OpenJarvis/*
