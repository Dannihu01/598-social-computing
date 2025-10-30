# utils/slack_api.py
import requests, logging, os
from typing import Dict

log = logging.getLogger("slack-ask-bot")

def post_to_response_url(response_url: str, text: str) -> None:
    """Post publicly to the invoking channel via response_url (no chat:write needed)."""
    r = requests.post(response_url, json={"response_type": "in_channel", "text": text}, timeout=15)
    r.raise_for_status()

def slack_api(method: str, payload: Dict) -> Dict:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing SLACK_BOT_TOKEN for Slack Web API method")
    log.debug("Using Slack bot token from environment for Web API method: %s", method)
    r = requests.post(
        f"https://slack.com/api/{method}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    response_json = r.json()
    if response_json.get("ok"):
        return response_json
    # Attempt one refresh on token errors if rotation is enabled
    if response_json.get("error") in {"invalid_auth", "token_expired"}:
        log.warning("Slack token invalid or expired (%s). Initiating refresh.", response_json.get("error"))
        
        refreshed = _try_refresh_bot_token()
        if refreshed:
            log.info("Slack access token refreshed. Retrying method: %s", method)
            r2 = requests.post(
                f"https://slack.com/api/{method}",
                headers={"Authorization": f"Bearer {refreshed}", "Content-Type": "application/json"},
                json=payload,
                timeout=15,
            )
            r2.raise_for_status()
            retry_json = r2.json()
            if retry_json.get("ok"):
                return retry_json
            log.error("Slack API retry after token refresh failed: %s", retry_json)
            return retry_json
    raise RuntimeError(f"Slack API error in {method}: {response_json}")

def _try_refresh_bot_token() -> str | None:
    """If refresh credentials exist, refresh and update env. Return new access token or None."""
    client_id = os.environ.get("SLACK_CLIENT_ID")
    client_secret = os.environ.get("SLACK_CLIENT_SECRET")
    refresh_token = os.environ.get("SLACK_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        log.debug("Skipping Slack token refresh: missing client credentials or refresh token.")
        return None
    log.info("Refreshing Slack access token via oauth.v2.access")
    r = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    r.raise_for_status()
    token_json = r.json()
    if not token_json.get("ok"):
        log.error("Slack token refresh failed: %s", token_json)
        return None
    new_access = token_json.get("access_token")
    new_refresh = token_json.get("refresh_token") or refresh_token
    if new_access:
        os.environ["SLACK_BOT_TOKEN"] = new_access
        os.environ["SLACK_REFRESH_TOKEN"] = new_refresh
        log.info("Slack access token updated in process environment.")
    return new_access

def open_im(user_id: str) -> str:
    """Return DM channel id (Dxxxxx) for a user."""
    return slack_api("conversations.open", {"users": user_id})["channel"]["id"]

def chat_post_message(channel: str, text: str) -> str:
    """Post as the bot (requires chat:write). Returns ts."""
    return slack_api("chat.postMessage", {"channel": channel, "text": text})["ts"]
