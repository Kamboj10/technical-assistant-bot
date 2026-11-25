# 🛠 Technical Troubleshooting Assistant

A chatbot that behaves like an **exact, point-to-point technical manual**. When you ask how to fix an error or install software/an OS (e.g. *"How to install Windows 11"*), it returns only the chronological micro-steps — every screen, button, selection, command, reboot, and wait state — with zero conversational filler, no theory, and no greetings. A single one-line `WARNING:` is emitted before any destructive action.

Two frontends are included: a **Streamlit** app (recommended) and a **Flask REST API + web UI**.

---

## ✨ Features

- Strict system prompt: numbered steps only, bold UI elements, one action per step, no questions, no sign-off.
- Pluggable LLM backends: **Groq**, **Ollama** (local), **OpenAI**.
- Live model selector (fetched from the provider API).
- Hyperparameter sliders (temperature, top_p, max_tokens, frequency/penalty).
- Editable system prompt with reset.
- Persistent chat sessions (save / load / delete) + Markdown export.
- Attach log/text files as context to a message.
- Per-message 👍/👎 feedback and regenerate.
- Streaming responses.

---

## 📁 Project Structure

```
.
├── app.py              # Streamlit UI (recommended)
├── api.py              # Flask REST API (SSE streaming)
├── frontend.html       # Web frontend for the Flask API
├── backend.py          # Reusable LLM client layer
├── storage.py          # Persistent chat sessions (JSON)
├── system_prompt.py    # Master system prompt
├── requirements.txt    # Python dependencies
├── .env.example        # Config template
├── .env                # Your secrets (gitignored)
├── .gitignore
└── README.md
```

---

## 🚀 Setup

### 1. Clone & enter the project
```bash
git clone <your-repo-url>
cd technical-troubleshooting-assistant
```

### 2. Create a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env        # macOS / Linux
# copy .env.example .env     # Windows
```
Edit `.env` and set your provider + API key:
```env
LLM_BACKEND=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```
Get a Groq key at https://console.groq.com/keys.  
For Ollama (local): set `LLM_BACKEND=ollama` and run `ollama pull llama3.1`.  
For OpenAI: set `LLM_BACKEND=openai` and `OPENAI_API_KEY=sk-...`.

---

## ▶️ Run

### Streamlit (recommended)
```bash
streamlit run app.py
```
Opens at http://localhost:8501.

### Flask API + web UI
```bash
python api.py
```
Opens at http://localhost:5000.  
REST endpoints:
- `GET /health` — health check
- `GET /providers` — list providers
- `GET /models?provider=groq` — list models
- `POST /chat` — streaming chat (SSE)

---

## ⚙️ Model Configuration (Hyperparameters)

| Param | Default | Purpose |
|---|---|---|
| `temperature` | `0.1` | Deterministic, prevents rambling |
| `top_p` | `0.9` | Focused nucleus sampling |
| `max_tokens` | `4096` | Prevents cut-off on long guides (raise to `8192` for full OS installs) |
| `frequency_penalty` | `0.2` | Reduces repeated steps |
| `presence_penalty` | `0.0` | Keeps steps sequential |
| `stream` | `True` | Live token streaming |

Recommended models (Groq): `qwen/qwen3.8-27b` (default), `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `allam-2-7b`.

---

## 🧠 How It Works

1. You type a question → appended to session history.
2. App builds `[system prompt] + [history]` and calls the LLM.
3. Tokens stream back live into the chat bubble.
4. Final response is saved to the session (JSON in `./sessions/`, gitignored).

The system prompt in `system_prompt.py` is the "personality contract" that forces step-only output.

---

## 📝 Notes

- Use `python`, not `python3`, on Windows.
- Activate `.venv` before running.
- Chat sessions contain your conversations — they are gitignored by default.
- Never commit `.env`; only `.env.example` is tracked.