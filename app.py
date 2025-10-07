# app.py
import os
import time
import hmac
import hashlib
import threading
import logging
from typing import Optional
from dotenv import load_dotenv

import requests
from flask import Flask, request, jsonify

import database.db as db

load_dotenv()
# ==== Environment / Config ====
# set in Render
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
# set in Render
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL", "gemini-2.5-flash")    # override if you want
PORT = int(os.environ.get("PORT", 8080))

# Optional: switch to REST instead of SDK by setting GEMINI_USE_REST=1
USE_REST = os.environ.get("GEMINI_USE_REST", "0") == "1"

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("slack-ask-bot")

# Flask app
app = Flask(__name__)

# initialize DB
dsn = f"dbname={os.environ.get('DATABASE_NAME')} user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']} host={os.environ['DATABASE_HOST']} port={os.environ.get('DATABASE_PORT',5432)}"

db.init_pool(dsn=dsn)

# ==== Slack signature verification ====


def verify_slack(req) -> bool:
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    sig = req.headers.get("X-Slack-Signature", "")
    if not ts or not sig:
        return False
    # prevent replay attacks (5m window)
    if abs(time.time() - int(ts)) > 60 * 5:
        return False
    body = req.get_data().decode("utf-8")
    base = f"v0:{ts}:{body}".encode("utf-8")
    my_sig = "v0=" + \
        hmac.new(SLACK_SIGNING_SECRET.encode("utf-8"),
                 base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(my_sig, sig)

# ==== Gemini clients ====


def ask_gemini_rest(prompt: str, model: Optional[str] = None, timeout: int = 20) -> str:
    """Call Gemini via REST (no SDK)."""
    model = model or GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json",
               "x-goog-api-key": GEMINI_API_KEY}
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


# Try SDK import if allowed
genai = None
model_obj = None
if not USE_REST:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)
        model_obj = genai.GenerativeModel(GEMINI_MODEL)
        log.info(f"Gemini SDK initialized with model: {GEMINI_MODEL}")
    except Exception as e:
        log.warning(
            f"Gemini SDK not available or failed to init ({e}); falling back to REST.")
        genai = None
        model_obj = None
        USE_REST = True


def ask_gemini(prompt: str) -> str:
    """Ask Gemini using SDK if available; otherwise REST."""
    try:
        if not USE_REST and model_obj is not None:
            resp = model_obj.generate_content(
                prompt)  # simple single-turn call
            text = getattr(resp, "text", "") or ""
            return text.strip()
        # REST fallback
        return ask_gemini_rest(prompt)
    except Exception as e:
        log.exception("Gemini call failed")
        return f"(Gemini error: {e})"

# ==== Helper: safe Slack post via response_url ====


def post_to_response_url(response_url: str, text: str) -> None:
    try:
        requests.post(response_url, json={
            "response_type": "in_channel",  # public message
            "text": text
        }, timeout=15)
    except Exception:
        log.exception("Failed posting to response_url")

# ==== Routes ====


@app.get("/")
def root():
    # Simple health page
    return jsonify({"ok": True, "service": "slack-ask-bot", "model": GEMINI_MODEL, "rest": USE_REST}), 200


@app.route("/slack/commands", methods=['POST'])
# def slack_command():
#     return "Command received", 200
def slash():
    # Verify Slack signature
    if not verify_slack(request):
        return "invalid signature", 401

    # Parse slash command payload (x-www-form-urlencoded)
    user_id = request.form.get("user_id", "")
    text = (request.form.get("text") or "").strip()
    response_url = request.form.get("response_url")

    # Basic usage help
    if not text:
        return jsonify({
            "response_type": "ephemeral",
            "text": "Usage: `/ask <prompt>`"
        }), 200

    if not response_url:
        # Shouldn't happen for real Slash Commands
        log.error("Missing response_url in Slack payload.")
        return jsonify({
            "response_type": "ephemeral",
            "text": "Error: missing response_url from Slack."
        }), 200

    # ACK immediately so Slack doesn't time out
    # Do the Gemini call + public post in the background
    def worker():
        log.info("Calling Gemini...")
        answer = ask_gemini(text)
        if not answer:
            answer = "(no answer)"
        message = f"<@{user_id}> asked: {text}\n\n*Gemini:* {answer}"
        post_to_response_url(response_url, message)
        log.info("Posted response to Slack.")

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({
        "response_type": "ephemeral",
        "text": "Thanks — working on it now. I'll post the result here when ready."
    }), 200


@app.route("/testing/db", methods=["GET"])
def testDB():
    conn = db.get_conn()            # borrow a connection from the pool
    cur = conn.cursor()
    cur.execute("SELECT uuid, slack_id FROM users LIMIT 50;")
    cols = [c[0] for c in cur.description]   # column names
    rows = cur.fetchall()
    # convert to list of dicts so jsonify returns nicer JSON
    results = [dict(zip(cols, r)) for r in rows]
    return jsonify({"ok": True, "rows": results}), 200

    # ==== Entrypoint ====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
