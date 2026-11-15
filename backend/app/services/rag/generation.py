"""
Answer generation via Gemini (Google AI Studio).

Sends the fully-built prompt to the generation model and parses the strict JSON
response into ``{"answer": ..., "detected_language": ...}``. The SDK is imported
lazily so importing the engine requires neither the SDK nor an API key.
"""

import json
import re

from app.config import settings

# Matches a ```json ... ``` (or plain ``` ... ```) fenced block, if the model
# wraps its JSON in markdown despite being asked not to.
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _parse_response(text: str) -> dict:
    raw = text.strip()
    m = _FENCE_RE.search(raw)
    if m:
        raw = m.group(1).strip()
    try:
        data = json.loads(raw)
        return {
            "answer": data.get("answer", ""),
            "detected_language": data.get("detected_language"),
        }
    except (json.JSONDecodeError, AttributeError):
        # Model didn't return clean JSON — fall back to the raw text as the answer.
        return {"answer": text.strip(), "detected_language": None}


def generate_answer(prompt: str) -> dict:
    """Call the generation model and return ``{"answer", "detected_language"}``."""
    from google import genai
    from google.genai import types

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set — configure it in backend/.env to generate answers."
        )
    # An explicit timeout keeps a slow/overloaded model from stalling the guest
    # request for minutes (the SDK retries transient errors with backoff).
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=settings.generation_timeout_seconds * 1000),
    )
    response = client.models.generate_content(
        model=settings.generation_model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=settings.generation_temperature),
    )
    return _parse_response(response.text)
