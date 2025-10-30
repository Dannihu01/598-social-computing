# utils/slack_api.py
import requests, logging
from typing import Dict
from config import SLACK_BOT_TOKEN
import os

from utils.slack_tokens import get_bot_token

log = logging.getLogger("slack-ask-bot")

def post_to_response_url(response_url: str, text: str) -> None:
    """Post publicly to the invoking channel via response_url (no chat:write needed)."""
    r = requests.post(response_url, json={"response_type": "in_channel", "text": text}, timeout=15)
    r.raise_for_status()

def slack_api(method: str, payload: Dict) -> Dict:
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("Missing SLACK_BOT_TOKEN for Slack Web API method")
    r = requests.post(
        f"https://slack.com/api/{method}",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Slack API error in {method}: {j}")
    return j

def open_im(user_id: str) -> str:
    """Return DM channel id (Dxxxxx) for a user."""
    return slack_api("conversations.open", {"users": user_id})["channel"]["id"]

def chat_post_message(channel: str, text: str) -> str:
    """Post as the bot (requires chat:write). Returns ts."""
    return slack_api("chat.postMessage", {"channel": channel, "text": text})["ts"]



log = logging.getLogger("slack-api")

SLACK_API_BASE = "https://slack.com/api"
TOKEN = os.getenv("SLACK_BOT_TOKEN")

def _headers():
    token = get_bot_token()  # short-lived xoxb from your refresh flow
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }

def open_im(user_id: str):
    """Open a DM channel with a user and return the channel ID."""
    url = f"{SLACK_API_BASE}/conversations.open"
    resp = requests.post(url, headers=_headers(), json={"users": user_id})
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error in conversations.open: {data}")
    return data["channel"]["id"]

def chat_post_message(channel_id: str, text: str):
    """Send a message to a channel (including DMs)."""
    url = f"{SLACK_API_BASE}/chat.postMessage"
    resp = requests.post(url, headers=_headers(), json={"channel": channel_id, "text": text})
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error in chat.postMessage: {data}")
    return data