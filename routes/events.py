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
    print("Inside process_dm_message")
    try:
        user_id = str(event.get("user"))
        print(f"userID: {user_id}")
        text = event.get("text", "")
        channel = event.get("channel")
        if not user_id or not text:
            return
             # Get or create user
        user = users.get_user_by_slack_id(user_id)
        if not user:
            print(f"user not present, creating...")
            user = users.create_user(user_id)


        # Check if there's an active event
        active_event = get_active_event()
        if not active_event:
            log.info(f"No active event, ignoring DM from {user_id}")
            return

        # Save the response to the database
        print("adding response...")
        result = add_response(user_slack_id=user_id, response=text)
       
        log.info(
            f"Saved DM response from {user_id} for event {active_event.id}: {text[:50]}...")

    except Exception as e:
        log.error(f"Error processing DM message: {e}")
        ##TODO: System notification to let user know their response is recorded
    return jsonify({"text": f"🎉 Message recorded"})


@events_bp.post("/events")
def slack_events():
    """Handle Slack Events API webhooks"""

    print("Received Slack event")

    # Slack sends a verification challenge on initial setup
    if request.json and request.json.get("type") == "url_verification":
        return jsonify({"challenge": request.json["challenge"]})

    # Verify signature for real events
    if not verify_slack(request):
        return "invalid signature", 401

    payload = request.json
    event = payload.get("event", {})
    event_type = event.get("type")
    
    # Debug logging
    print(f"Event type: {event_type}")
    print(f"Event channel_type: {event.get('channel_type')}")
    print(f"Event channel: {event.get('channel')}")
    print(f"Full event: {event}")
    
    # Ignore bot's own messages
    if event.get("bot_id"):
        print("Ignoring bot message")
        return "", 200

    # Handle different event types
    if event_type == "message":
        # Ignore message_changed, message_deleted, etc.
        if event.get("subtype"):
            print(f"Ignoring message subtype: {event.get('subtype')}")
            return "", 200
            
        channel = event.get("channel", "")
        channel_type = event.get("channel_type")
        
        # DMs have channel_type="im" OR channel starting with "D"
        is_dm = channel_type == "im" or (channel and channel.startswith("D"))
        
        print(f"Message event - channel: {channel}, channel_type: {channel_type}, is_dm: {is_dm}")
        
        if is_dm:
            print("Processing as DM")
            process_dm_message(event)
        # Check if it's in a thread
        elif event.get("thread_ts"):
            print("Processing as thread message")
            process_message_event(event)

    elif event_type == "reaction_added":
        # Track reactions as engagement signals
        if event.get("item", {}).get("type") == "message":
            process_reaction_event(event)

    # Acknowledge receipt immediately
    return "", 200


