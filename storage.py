"""Persistent chat sessions stored as JSON files in ./sessions."""

import json
import os
import uuid
from datetime import datetime

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


def _path(sid: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{sid}.json")


def list_sessions() -> list[dict]:
    out = []
    for f in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(SESSIONS_DIR, f), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            out.append({
                "id": data.get("id"),
                "title": data.get("title", "Untitled"),
                "updated": data.get("updated", ""),
                "count": len(data.get("messages", [])),
            })
        except Exception:
            continue
    return out


def new_session(title: str = "New chat") -> str:
    sid = uuid.uuid4().hex[:12]
    save_session(sid, [], title)
    return sid


def save_session(sid: str, messages: list, title: str | None = None) -> None:
    path = _path(sid)
    existing = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            existing = json.load(fh)
    data = {
        "id": sid,
        "title": title or existing.get("title", "New chat"),
        "created": existing.get("created", datetime.now().isoformat(timespec="seconds")),
        "updated": datetime.now().isoformat(timespec="seconds"),
        "messages": messages,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def load_session(sid: str) -> dict | None:
    path = _path(sid)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def delete_session(sid: str) -> bool:
    path = _path(sid)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def export_markdown(messages: list) -> str:
    lines = ["# Technical Troubleshooting Chat", ""]
    for m in messages:
        role = "You" if m["role"] == "user" else "Assistant"
        lines.append(f"## {role}")
        lines.append(m["content"])
        lines.append("")
    return "\n".join(lines)
