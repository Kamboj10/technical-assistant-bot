"""Interactive Streamlit chat UI for the Technical Troubleshooting Assistant."""

import json
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from backend import (PROVIDERS, get_provider, get_model, list_models,
                     stream_chat)


@st.cache_data(ttl=300, show_spinner=False)
def cached_models(provider: str):
    try:
        return list_models(provider)
    except Exception:
        return []


@st.cache_data(ttl=2, show_spinner=False)
def cached_sessions():
    return list_sessions()
from system_prompt import SYSTEM_PROMPT
from storage import (list_sessions, new_session, save_session, load_session,
                     delete_session, export_markdown)

load_dotenv()

st.set_page_config(page_title="Technical Troubleshooting Assistant",
                   page_icon="🛠", layout="wide")

# ---------- Wallpaper / design CSS ----------
st.markdown("""
<style>
.stApp {
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #fdf2f8 100%);
  background-attachment: fixed;
}
.stApp::before {
  content: "";
  position: fixed; inset: 0;
  background-image: radial-gradient(rgba(99,102,241,0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  pointer-events: none; z-index: 0;
}
[data-testid="stSidebar"] {
  background: rgba(255,255,255,0.65);
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(99,102,241,0.12);
}
[data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(99,102,241,0.12);
  border-radius: 14px;
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(99,102,241,0.05);
}
h1, .stMarkdown h1 {
  background: linear-gradient(90deg, #4f46e5, #ec4899);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.stButton > button {
  border-radius: 10px; border: 1px solid rgba(99,102,241,0.2);
  background: rgba(99,102,241,0.1); color: #1e1b4b;
  transition: all .15s ease;
}
.stButton > button:hover {
  background: rgba(99,102,241,0.22); transform: translateY(-1px);
}
.stDownloadButton > button { background: rgba(34,197,94,0.12); color: #14532d; }
.stTextInput > div > div > input, .stTextArea textarea {
  background: rgba(255,255,255,0.8); border-radius: 10px; color: #1e1b4b;
}
/* text color on light bg */
.stMarkdown, .stCaption, p, label, .stChatMessage { color: #1e1b4b; }
</style>
""", unsafe_allow_html=True)

# ---------- Session state defaults ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = new_session()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "params" not in st.session_state:
    st.session_state.params = {
        "temperature": 0.1, "top_p": 0.9, "max_tokens": 4096,
        "frequency_penalty": 0.2, "presence_penalty": 0.0,
    }
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = SYSTEM_PROMPT
if "provider" not in st.session_state:
    st.session_state.provider = get_provider()
if "model" not in st.session_state:
    st.session_state.model = get_model(st.session_state.provider)
if "feedback" not in st.session_state:
    st.session_state.feedback = {}
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

def now_ts():
    return datetime.now().strftime("%H:%M")

# ---------- Sidebar ----------
with st.sidebar:
    st.title("⚙️ Controls")

    st.subheader("Provider")
    provider = st.selectbox("LLM backend", list(PROVIDERS.keys()),
                            index=list(PROVIDERS.keys()).index(st.session_state.provider)
                            if st.session_state.provider in PROVIDERS else 0)
    if provider != st.session_state.provider:
        st.session_state.provider = provider
        st.session_state.model = get_model(provider)
        st.rerun()

    st.subheader("Model")
    models = cached_models(provider)
    if models:
        idx = models.index(st.session_state.model) if st.session_state.model in models else 0
        model = st.selectbox("Model", models, index=idx)
    else:
        model = st.text_input("Model (manual)", value=st.session_state.model)
    if model != st.session_state.model:
        st.session_state.model = model

    st.subheader("Hyperparameters")
    p = st.session_state.params
    p["temperature"] = st.slider("temperature", 0.0, 1.0, p["temperature"], 0.05)
    p["top_p"] = st.slider("top_p", 0.1, 1.0, p["top_p"], 0.05)
    p["max_tokens"] = st.slider("max_tokens", 256, 8192, p["max_tokens"], 256)
    p["frequency_penalty"] = st.slider("frequency_penalty", 0.0, 2.0, p["frequency_penalty"], 0.1)
    p["presence_penalty"] = st.slider("presence_penalty", 0.0, 2.0, p["presence_penalty"], 0.1)

    with st.expander("📝 System prompt", expanded=False):
        edited = st.text_area("Edit", value=st.session_state.system_prompt, height=220)
        c1, c2 = st.columns(2)
        if c1.button("Apply"):
            st.session_state.system_prompt = edited
            st.success("Applied")
        if c2.button("Reset default"):
            st.session_state.system_prompt = SYSTEM_PROMPT
            st.rerun()

    st.subheader("Sessions")
    sessions = cached_sessions()
    ids = [s["id"] for s in sessions]
    if ids:
        cur_idx = ids.index(st.session_state.session_id) if st.session_state.session_id in ids else 0
        chosen = st.selectbox("Load session", ids, index=cur_idx,
                              format_func=lambda x: next((f"{s['title']} ({s['count']})" for s in sessions if s["id"] == x), x))
        if chosen != st.session_state.session_id:
            data = load_session(chosen)
            if data:
                st.session_state.session_id = chosen
                st.session_state.messages = data.get("messages", [])
                st.rerun()
    c1, c2 = st.columns(2)
    if c1.button("➕ New"):
        st.session_state.session_id = new_session()
        st.session_state.messages = []
        st.session_state.feedback = {}
        cached_sessions.clear()
        st.rerun()
    if c2.button("🗑 Delete"):
        delete_session(st.session_state.session_id)
        st.session_state.session_id = new_session()
        st.session_state.messages = []
        cached_sessions.clear()
        st.rerun()

    if st.session_state.messages:
        md = export_markdown(st.session_state.messages)
        st.download_button("⬇ Export chat (.md)", data=md,
                           file_name=f"chat_{st.session_state.session_id}.md",
                           mime="text/markdown")

    st.subheader("Attach file")
    uploaded = st.file_uploader("Log / text file", type=["txt", "log", "md", "json", "csv"])
    if uploaded is not None:
        content = uploaded.read().decode("utf-8", errors="replace")
        st.session_state["pending_file"] = (uploaded.name, content)
        st.caption(f"Attached: {uploaded.name} ({len(content)} chars)")

    st.markdown("---")
    st.caption(f"Provider: `{provider}`  \nModel: `{st.session_state.model}`  \nSession: `{st.session_state.session_id}`")

# ---------- Main ----------
st.title("🛠 Technical Troubleshooting Assistant")
st.caption("Exact, point-to-point technical steps. No filler. Edit controls in the sidebar.")

# Quick prompt chips
st.markdown("**Quick prompts:**")
qp_cols = st.columns(4)
quick_prompts = ["How to install Windows 11", "Fix blue screen (BSOD)", "Install Python on Windows", "Reset Windows password"]
for i, q in enumerate(quick_prompts):
    if qp_cols[i].button(q, key=f"qp_{i}"):
        st.session_state.pending_prompt = q
        st.rerun()

# Render history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        ts = msg.get("ts", "")
        if ts:
            st.caption(f"🕐 {ts}")
        if msg["role"] == "assistant":
            cols = st.columns([1, 1, 1, 5])
            fb = st.session_state.feedback.get(i)
            if cols[0].button("👍", key=f"up_{i}"):
                st.session_state.feedback[i] = "up"
                st.rerun()
            if cols[1].button("👎", key=f"down_{i}"):
                st.session_state.feedback[i] = "down"
                st.rerun()
            if cols[2].button("📋", key=f"copy_{i}"):
                components.html(f"""
                <script>navigator.clipboard.writeText({json.dumps(msg['content'])});</script>
                """, height=0)
                st.toast("Copied to clipboard")
            if fb:
                st.caption(f"Feedback: {fb}")

def run_generation():
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🤔 *Thinking…*")
        full = ""
        try:
            for delta in stream_chat(
                st.session_state.provider,
                st.session_state.model,
                [{"role": "system", "content": st.session_state.system_prompt}] + st.session_state.messages,
                st.session_state.params["temperature"],
                st.session_state.params["top_p"],
                st.session_state.params["max_tokens"],
                st.session_state.params["frequency_penalty"],
                st.session_state.params["presence_penalty"],
            ):
                full += delta
                placeholder.markdown(full)
        except Exception as e:
            full = f"ERROR: {e}"
            placeholder.error(full)

        if full:
            st.session_state.messages.append({"role": "assistant", "content": full, "ts": now_ts()})
            sess = load_session(st.session_state.session_id)
            title = st.session_state.messages[0]["content"][:40] if (sess and sess.get("title") == "New chat") else None
            save_session(st.session_state.session_id, st.session_state.messages, title=title)
            cached_sessions.clear()
    st.rerun()

# Handle pending quick prompt
pending_prompt = st.session_state.pop("pending_prompt", None)
prompt = st.chat_input("Describe the error or task (e.g. 'How to install Windows 11')...")
if pending_prompt and not prompt:
    prompt = pending_prompt

pending = st.session_state.pop("pending_file", None)

if prompt:
    user_content = prompt
    if pending:
        name, content = pending
        user_content = f"{prompt}\n\n--- Attached file: {name} ---\n{content}\n--- End of file ---"
    ts = now_ts()
    st.session_state.messages.append({"role": "user", "content": user_content, "ts": ts})
    with st.chat_message("user"):
        st.markdown(user_content)
        st.caption(f"🕐 {ts}")
    run_generation()

# Regenerate last response
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    if st.button("🔄 Regenerate last response"):
        st.session_state.messages.pop()
        save_session(st.session_state.session_id, st.session_state.messages)
        run_generation()
