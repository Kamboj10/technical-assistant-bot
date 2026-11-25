"""Flask backend exposing a streaming chat API (alternative to the Streamlit app)."""

import json
import os
from flask import Flask, Response, request, jsonify, send_from_directory
from dotenv import load_dotenv

from backend import (PROVIDERS, get_provider, get_model, list_models, stream_chat)

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")


@app.route("/")
def index():
    return send_from_directory(".", "frontend.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/providers")
def providers():
    return jsonify(list(PROVIDERS.keys()))


@app.route("/models")
def models():
    provider = request.args.get("provider", get_provider())
    try:
        return jsonify(list_models(provider))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    provider = data.get("provider", get_provider())
    model = data.get("model", get_model(provider))
    messages = data.get("messages", [])
    system_prompt = data.get("system_prompt")
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + [
            m for m in messages if m.get("role") != "system"
        ]
    params = data.get("params", {})
    temperature = params.get("temperature", 0.1)
    top_p = params.get("top_p", 0.9)
    max_tokens = params.get("max_tokens", 4096)
    frequency_penalty = params.get("frequency_penalty", 0.2)
    presence_penalty = params.get("presence_penalty", 0.0)

    def generate():
        try:
            for delta in stream_chat(provider, model, messages, temperature, top_p,
                                    max_tokens, frequency_penalty, presence_penalty):
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
