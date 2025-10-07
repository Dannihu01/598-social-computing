# --------------------------------------------------
# File: services/gemini_client.py
# Description: Provides an interface to the Gemini API for text generation,
# supporting both the official SDK and REST fallback modes.
# --------------------------------------------------


import json, logging, requests
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_USE_REST

log = logging.getLogger("slack-ask-bot")

_genai = None
_model_obj = None
if GEMINI_API_KEY and not GEMINI_USE_REST:
    try:
        import google.genai as genai  # type: ignore
        
        _genai = GEMINI_MODEL
        _model_obj = genai.Client(api_key=GEMINI_API_KEY)
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
            resp = _model_obj.models.generate_content(contents=prompt, model=_genai)
            return (getattr(resp, "text", "") or "").strip()
        return _rest_call(prompt)
    except Exception as e:
        log.exception("Gemini call failed")
        return f"(Gemini error: {e})"

def ask_gemini_structured(
    prompt: str,
    schema: dict | None = None,
    mime_type: str = "application/json",
    timeout: int = 20,
) -> object:
    config: dict[str, object] = {}
    if mime_type:
        config["response_mime_type"] = mime_type
    if schema:
        config["response_schema"] = schema

    try:
        if _model_obj is not None:
            response = _model_obj.models.generate_content(
                contents=prompt,
                model=_genai,
                config=config or None,
            )
            text_payload = (getattr(response, "text", "") or "").strip()
            if mime_type == "application/json":
                try:
                    return json.loads(text_payload) if text_payload else {}
                except json.JSONDecodeError:
                    log.warning("Structured response was not valid JSON; returning raw text.")
            return text_payload

        return _rest_call_structured(prompt, schema, mime_type, timeout=timeout)
    except Exception:
        log.exception("Gemini structured call failed")
        return None


def _rest_call_structured(
    prompt: str,
    schema: dict | None,
    mime_type: str,
    timeout: int = 20,
) -> object:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    generation_config: dict[str, object] = {}
    if mime_type:
        generation_config["responseMimeType"] = mime_type
    if schema:
        generation_config["responseSchema"] = schema

    payload: dict[str, object] = {"contents": [{"parts": [{"text": prompt}]}]}
    if generation_config:
        payload["generationConfig"] = generation_config

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    body = resp.json()

    text_payload = (
        body.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    ).strip()

    if mime_type == "application/json":
        try:
            return json.loads(text_payload) if text_payload else {}
        except json.JSONDecodeError:
            log.warning("REST structured response was not valid JSON; returning raw text.")
    return text_payload
