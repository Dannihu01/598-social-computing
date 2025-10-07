# --------------------------------------------------
# File: services/gemini_client.py
# Description: Provides an interface to the Gemini API for text generation,
# supporting both the official SDK and REST fallback modes.
# --------------------------------------------------


import logging, requests
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_USE_REST

log = logging.getLogger("slack-ask-bot")

_genai = None
_model_obj = None

if GEMINI_API_KEY and not GEMINI_USE_REST:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)
        _genai = genai
        _model_obj = genai.GenerativeModel(GEMINI_MODEL)
        log.info(f"Gemini SDK ready: {GEMINI_MODEL}")
    except Exception as e:
        log.warning(f"Gemini SDK init failed: {e}; falling back to REST.")
        _genai = None
        _model_obj = None


def _rest_call(prompt: str, timeout: int = 20) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    try:
        return (
            j.get("candidates", [{}])[0]
             .get("content", {})
             .get("parts", [{}])[0]
             .get("text", "")
        ).strip()
    except Exception:
        return ""


def ask_gemini(prompt: str) -> str:
    try:
        if _model_obj is not None:
            resp = _model_obj.generate_content(prompt)
            return (getattr(resp, "text", "") or "").strip()
        return _rest_call(prompt)
    except Exception as e:
        log.exception("Gemini call failed")
        return f"(Gemini error: {e})"
