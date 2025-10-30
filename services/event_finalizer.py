# --------------------------------------------------
# File: services/event_finalizer.py
# Description: Finalize events by creating channels for user groups
# --------------------------------------------------

import logging
from typing import Dict, List
from database.repos.responses import get_responses_with_users
from services.response_classifier import classify_user_responses
from services.channel_generator import generate_channel_metadata
from utils.slack_api import create_channel, invite_users_to_channel, chat_post_message

log = logging.getLogger("event-finalizer")


def finalize_event(event_id: int) -> Dict:
    """
    Complete an event by grouping users, creating channels, and inviting participants.
    
    Args:
        event_id: The event to finalize
        
    Returns:
        Dict with summary: {
            "success": bool,
            "groups_created": int,
            "channels_created": List[str],
            "errors": List[str]
        }
    """
    summary = {
        "success": False,
        "groups_created": 0,
        "channels_created": [],
        "errors": []
    }
    
    try:
        log.info(f"Starting finalization for event {event_id}")
        
        # Step 1: Classify users into groups
        groups = classify_user_responses(event_id)
        
        if not groups:
            summary["errors"].append("No valid groups found from classification")
            log.warning(f"Event {event_id}: No valid groups to process")
            return summary
        
        summary["groups_created"] = len(groups)
        log.info(f"Event {event_id}: Processing {len(groups)} groups")
        
        # Get all responses for this event
        all_responses = get_responses_with_users(event_id)
        responses_dict = {slack_id: entry for slack_id, entry in all_responses}
        
        # Step 2 & 3: For each group, generate metadata and create channel
        for i, group_slack_ids in enumerate(groups, 1):
            try:
                log.info(f"Processing group {i}/{len(groups)} with {len(group_slack_ids)} users")
                
                # Get responses for this specific group
                user_responses = [
                    (slack_id, responses_dict.get(slack_id, ""))
                    for slack_id in group_slack_ids
                    if slack_id in responses_dict
                ]
                
                if not user_responses:
                    summary["errors"].append(f"Group {i}: No responses found for users")
                    continue
                
                # Generate channel metadata
                metadata = generate_channel_metadata(user_responses)
                if not metadata:
                    summary["errors"].append(f"Group {i}: Failed to generate metadata")
                    continue
                
                # Create unique channel name with event ID
                channel_name = f"{metadata['channel_name']}-event{event_id}"
                
                # Create Slack channel
                try:
                    channel_info = create_channel(channel_name, is_private=False)
                    channel_id = channel_info["id"]
                    log.info(f"Created channel {channel_id} ({channel_name})")
                    
                    # Invite users to channel
                    invite_users_to_channel(channel_id, group_slack_ids)
                    log.info(f"Invited {len(group_slack_ids)} users to {channel_id}")
                    
                    # Post welcome message
                    mentions = " ".join([f"<@{sid}>" for sid in group_slack_ids])
                    full_message = (
                        f"👋 {mentions}\n\n"
                        f"{metadata['initial_message']}\n\n"
                        f"💬 {metadata['call_to_action']}"
                    )
                    chat_post_message(channel_id, full_message)
                    log.info(f"Posted welcome message to {channel_id}")
                    
                    summary["channels_created"].append(channel_id)
                    
                except Exception as e:
                    error_msg = f"Group {i}: Failed to create/setup channel - {str(e)}"
                    summary["errors"].append(error_msg)
                    log.error(error_msg)
            
            except Exception as e:
                error_msg = f"Group {i}: Unexpected error - {str(e)}"
                summary["errors"].append(error_msg)
                log.error(error_msg)
        
        # Mark as successful if at least one channel was created
        summary["success"] = len(summary["channels_created"]) > 0
        
        log.info(f"Event {event_id} finalization complete: "
                f"{len(summary['channels_created'])} channels created, "
                f"{len(summary['errors'])} errors")
        
        return summary
    
    except Exception as e:
        error_msg = f"Critical error finalizing event {event_id}: {str(e)}"
        summary["errors"].append(error_msg)
        log.error(error_msg)
        return summary
