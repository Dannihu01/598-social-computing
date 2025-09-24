import os, time, hmac, hashlib
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
app = Flask(__name__)

def verify_slack(req):
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    sig = req.headers.get("X-Slack-Signature", "")
    if not ts or not sig:
        return False
    if abs(time.time() - int(ts)) > 60*5:
        return False
    body = req.get_data().decode("utf-8")
    base = f"v0:{ts}:{body}".encode("utf-8")
    my_sig = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode("utf-8"),
        base,
        hashlib.sha256
    ).hexdigest()
    # constant-time compare
    return hmac.compare_digest(my_sig, sig)

@app.post("/slack/commands")
def slash():
    if not verify_slack(request):
        return "invalid signature", 401

    user_id = request.form.get("user_id")
    text = (request.form.get("text") or "").strip() or "(no message provided)"
    response_url = request.form["response_url"]

    # ACK within 3s
    # You can also respond inline with JSON instead of delayed post.
    # Here we ACK empty, then use response_url to post publicly.
    requests.post(response_url, json={
        "response_type": "in_channel",
        "text": f"<!@{user_id}> asked: {text}",
    })
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
