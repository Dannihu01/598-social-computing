import os
import time
import hmac
import hashlib
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai  # assumes the SDK

# Slack secret & Gemini key from env
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")  # needed if posting using chat.postMessage
GEN_API_KEY = os.environ["GEMINI_API_KEY"]

app = Flask(__name__)

# configure Gemini SDK
genai.configure(api_key=GEN_API_KEY)

def verify_slack(req):
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    sig = req.headers.get("X-Slack-Signature", "")
    if not ts or not sig:
        return False
    # prevent replay
    if abs(time.time() - int(ts)) > 60 * 5:
        return False
    body = req.get_data().decode("utf-8")
    base = f"v0:{ts}:{body}".encode("utf-8")
    my_sig = "v0=" + hmac.new(SLACK_SIGNING_SECRET.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(my_sig, sig)

@app.post("/slack/commands")
def slash():
    # Verify request
    if not verify_slack(request):
        return "invalid signature", 401

    user_id = request.form.get("user_id")
    text = (request.form.get("text") or "").strip()
    response_url = request.form["response_url"]

    if not text:
        # early return
        return jsonify({
            "response_type": "ephemeral",
            "text": "You didn’t provide a prompt."
        }), 200

    # Option A: synchronous call (if Gemini is fast)
    try:
        resp = genai.models.generate_content(
            model="gemini-2.5-flash",  # or whichever model
            contents=text
        )
        answer = resp.text
    except Exception as e:
        answer = f"Error calling Gemini: {str(e)}"

    # Send back to Slack publicly
    # Using response_url
    requests.post(response_url, json={
        "response_type": "in_channel",
        "text": f"<@{user_id}> asked: {text}\n\n*Gemini says:* {answer}"
    })

    # immediate ACK
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
