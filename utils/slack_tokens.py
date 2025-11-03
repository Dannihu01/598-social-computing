# utils/slack_tokens.py
import os, time, threading
import requests

_LOCK = threading.Lock()
_state = {
    "access_token": None,
    "expires_at": 0,
    "refresh_token": os.getenv("SLACK_REFRESH_TOKEN"),
}

CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

def _refresh():
    r = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": _state["refresh_token"],
        },
        timeout=10,
    ).json()
    if not r.get("ok"):
        raise RuntimeError(f"Slack refresh failed: {r}")
    _state["access_token"] = r["access_token"]       # xoxb-...
    _state["expires_at"]   = int(time.time()) + int(r["expires_in"])
    # Slack may rotate your refresh_token; persist it if returned:
    if "refresh_token" in r and r["refresh_token"]:
        _state["refresh_token"] = r["refresh_token"]

def get_bot_token():
    with _LOCK:
        if not _state["access_token"] or time.time() >= _state["expires_at"] - 60:
            _refresh()
        return _state["access_token"]
