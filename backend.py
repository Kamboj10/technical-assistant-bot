"""Reusable LLM backend: client factory, model listing, streaming chat."""

import os
from typing import Iterator
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "env_model": "GROQ_MODEL",
        "default_model": "qwen/qwen3.8-27b",
        "env_base": "GROQ_BASE_URL",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "env_key": "OLLAMA_API_KEY",
        "env_model": "OLLAMA_MODEL",
        "default_model": "llama3.1",
        "env_base": "OLLAMA_BASE_URL",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "env_model": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
        "env_base": "OPENAI_BASE_URL",
    },
}


def get_provider() -> str:
    return os.getenv("LLM_BACKEND", "groq").strip().lower()


def get_client(provider: str | None = None) -> OpenAI:
    provider = (provider or get_provider()).lower()
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    cfg = PROVIDERS[provider]
    base_url = os.getenv(cfg["env_base"], cfg["base_url"])
    api_key = os.getenv(cfg["env_key"], "ollama" if provider == "ollama" else "")
    if not api_key:
        raise ValueError(f"Missing API key for {provider}: set {cfg['env_key']} in .env")
    return OpenAI(base_url=base_url, api_key=api_key)


def get_model(provider: str | None = None) -> str:
    provider = (provider or get_provider()).lower()
    cfg = PROVIDERS[provider]
    return os.getenv(cfg["env_model"], cfg["default_model"])


def list_models(provider: str | None = None) -> list[str]:
    client = get_client(provider)
    try:
        return sorted(m.id for m in client.models.list().data)
    except Exception:
        return []


def stream_chat(provider, model, messages, temperature, top_p, max_tokens,
                frequency_penalty, presence_penalty) -> Iterator[str]:
    client = get_client(provider)
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def chat(provider, model, messages, temperature, top_p, max_tokens,
         frequency_penalty, presence_penalty) -> str:
    return "".join(stream_chat(provider, model, messages, temperature, top_p,
                               max_tokens, frequency_penalty, presence_penalty))
