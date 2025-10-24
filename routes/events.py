import logging
from flask import Blueprint, request, jsonify
from utils.verify import verify_slack
from services.thread_monitor import process_message_event, process_reaction_event
from database.repos import users, responses
from database.repos.events import get_active_event

from database.repos.responses import add_response

log = logging.getLogger("slack-ask-bot")
events_bp = Blueprint("events_bp", __name__, url_prefix="/slack")


def process_dm_message(event):
    """Process direct message events"""
    try:
        user_id = event.get("user")
        text = event.get("text", "")
        channel = event.get("channel")

        if not user_id or not text:
            return

        # Get or create user
        user = users.get_user_by_slack_id(user_id)
        if not user:
            user = users.create_user(user_id)

        # Check if there's an active event
        active_event = get_active_event()
        if not active_event:
            log.info(f"No active event, ignoring DM from {user_id}")
            return

        # Save the response to the database

        result = add_response(user_slack_id=user_id, response=text)

        log.info(
            f"Saved DM response from {user_id} for event {active_event.id}: {text[:50]}...")

    except Exception as e:
        log.error(f"Error processing DM message: {e}")


@events_bp.post("/events")
def slack_events():
    """Handle Slack Events API webhooks"""

    # Slack sends a verification challenge on initial setup
    if request.json and request.json.get("type") == "url_verification":
        return jsonify({"challenge": request.json["challenge"]})

    # Verify signature for real events
    if not verify_slack(request):
        return "invalid signature", 401

    payload = request.json
    event = payload.get("event", {})
    event_type = event.get("type")
    print(f"Received event: {event}")
    # Ignore bot's own messages
    if event.get("bot_id"):
        return "", 200

    # Handle different event types
    if event_type == "message":
        # Check if it's a DM (direct message)
        if event.get("channel_type") == "im":
            process_dm_message(event)
        # Check if it's in a thread
        elif event.get("thread_ts"):
            process_message_event(event)

    elif event_type == "reaction_added":
        # Track reactions as engagement signals
        if event.get("item", {}).get("type") == "message":
            process_reaction_event(event)

    # Acknowledge receipt immediately
    return "", 200


