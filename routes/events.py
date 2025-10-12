import logging
from flask import Blueprint, request, jsonify
from utils.verify import verify_slack
from services.thread_monitor import process_message_event, process_reaction_event

log = logging.getLogger("slack-ask-bot")
events_bp = Blueprint("events_bp", __name__, url_prefix="/slack")

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
        # Check if it's in a thread
        if event.get("thread_ts"):
            process_message_event(event)
    
    elif event_type == "reaction_added":
        # Track reactions as engagement signals
        if event.get("item", {}).get("type") == "message":
            process_reaction_event(event)
    
    # Acknowledge receipt immediately
    return "", 200