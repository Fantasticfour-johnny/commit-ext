# fastapi_commit_proxy.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# Allow requests from anywhere for MVP (later restrict to your extension)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 Store your API key securely (never put in client)
API_KEY = os.getenv("A4F_API_KEY", "your_api_key_here")
BASE_URL = "https://api.a4f.co/v1"

# ============================
# Model Registry (for MVP)
# ============================
# Syntax: provider-{number}/{model_name}
AI_MODELS = {
    # 🧠 Thinking / Reasoning Models
    "reasoning": [
        "provider-1/deepseek-r1-distill-llama-8b",
        "provider-1/deepseek-r1-distill-qwen-1.5b",
        "provider-3/deepseek-v3",
        "provider-3/deepseek-v3-0324",
        "provider-1/deepseek-v3.1-turbo"
    ],
    # 💬 Text / Chat Models (ideal for commit messages)
    "text": [
        "provider-3/llama-3.3-70b",
        "provider-3/gpt-4o-mini",
        "provider-3/gpt-4.1-nano",
        "provider-3/qwen-2.5-72b",
        "provider-3/gpt-5-nano"
    ],
    # 🎨 Image Generation Models (not used here)
    "image": [
        "provider-4/imagen-3",
        "provider-4/imagen-4",
        "provider-4/qwen-image"
    ],
    # 🔗 Embedding Models (optional)
    "embedding": [
        "provider-6/qwen3-embedding-4b",
        "provider-6/cliptagger-12b"
    ]
}

# Default model for MVP commit message generation
DEFAULT_MODEL = AI_MODELS["text"][0]  # "provider-3/llama-3.3-70b"


@app.post("/generate_commit")
async def generate_commit(request: Request):
    payload = await request.json()
    diff_text = payload.get("diff", "").strip()
    model_to_use = payload.get("model", DEFAULT_MODEL)

    if not diff_text:
        return {"error": "No diff provided."}

    # Call the A4F API
    try:
        response = requests.post(
            f"{BASE_URL}/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model_to_use,
                "prompt": f"Generate a concise Git commit message for the following code changes:\n{diff_text}",
                "max_tokens": 60
            },
            timeout=15  # avoid long hangs
        )
    except Exception as e:
        return {"error": "Failed to reach AI API", "details": str(e)}

    if response.status_code != 200:
        return {"error": "AI API request failed", "details": response.text}

    result = response.json()
    commit_message = result.get("choices", [{}])[0].get("text", "").strip()

    return {"commit_message": commit_message, "model_used": model_to_use}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
