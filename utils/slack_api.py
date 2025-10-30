# utils/slack_api.py
import requests, logging
from typing import Dict
from config import SLACK_BOT_TOKEN

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

def create_channel(name: str, is_private: bool = False) -> Dict:
    """
    Create a new Slack channel.
    
    Args:
        name: Channel name (lowercase, hyphens, max 80 chars)
        is_private: Whether channel is private (default: False)
        
    Returns:
        Channel info dict with 'id', 'name', etc.
    """
    result = slack_api("conversations.create", {
        "name": name,
        "is_private": is_private
    })
    return result["channel"]

def invite_users_to_channel(channel_id: str, user_ids: list) -> Dict:
    """
    Invite multiple users to a channel.
    
    Args:
        channel_id: The channel ID (C...)
        user_ids: List of user slack_ids (U...)
        
    Returns:
        API response dict
    """
    return slack_api("conversations.invite", {
        "channel": channel_id,
        "users": ",".join(user_ids)
    })
