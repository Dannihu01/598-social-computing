# --------------------------------------------------
# File: routes/commands.py
# Description: Defines Flask routes for Slack slash commands, including
# /dm_test, /announce, and /ask. Handles Slack verification, message
# posting, and asynchronous Gemini API responses.
# --------------------------------------------------

import re
import threading
import logging
from flask import Blueprint, request, jsonify
from utils.verify import verify_slack
from utils.slack_api import post_to_response_url, open_im, chat_post_message
from services.gemini_client import ask_gemini, ask_gemini_structured

from database.repos import responses, users, enterprises, messages, events
from services.event_finalizer import finalize_event
log = logging.getLogger("slack-ask-bot")
commands_bp = Blueprint("commands_bp", __name__, url_prefix="/slack")


@commands_bp.post("/commands")
def slash():
    if not verify_slack(request):
        return "invalid signature", 401

    command = request.form.get("command", "")
    user_id = request.form.get("user_id", "")
    channel_id = request.form.get("channel_id", "")
    enterprise_name = request.form.get("enterprise_name", "")
    text = (request.form.get("text") or "").strip()
    response_url = request.form.get("response_url")

    if not response_url:
        return jsonify({"response_type": "ephemeral", "text": "Missing response_url from Slack."}), 200

    # ---------- /dm_test ----------
    if command == "/dm_test":
        print(f"dm_test command received - text: '{text}'")
        log.info(f"dm_test command from user {user_id} with text: '{text}'")

        # users_list = users.list_users()
        # TODO: Get users from DB and do this action
        # TODO (stretch): Automatically send dms based on a criteria (webhook/automated runs)
        m = re.search(r"<@([A-Z0-9]+)(?:\|[^>]+)?>", text)
        if not m:
            print("No user mentioned in dm_test command")
            return jsonify({"text": "Usage: /dm_test @user your message"}), 200

        target = m.group(1)
        msg = text[m.end():].strip()
        print(f"Target user: {target}, Message: '{msg}'")

        if not msg:
            return jsonify({"text": "Please include a message."}), 200

        try:
            print(f"Opening IM with user {target}")
            dm_channel = open_im(target)
            print(f"DM channel opened: {dm_channel}")

            print(f"Sending message to channel {dm_channel}: '{msg}'")
            chat_post_message(dm_channel, msg)
            print("Message sent successfully")

            return jsonify({"text": f"DM sent to <@{target}>"}), 200
        except Exception as e:
            print(f"Error in dm_test: {e}")
            log.error(f"Error in dm_test: {e}")
            return jsonify({"text": f"Failed to send DM: {str(e)}"}), 200

    # ---------- /announce ----------
    # Usage: /announce @user [@user2 ...] Your announcement
    if command == "/announce":
        mentioned_ids = re.findall(r"<@([A-Z0-9]+)>", text)
        body = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()
        if not mentioned_ids or not body:
            return jsonify({"response_type": "ephemeral", "text": "Usage: `/announce @user [@user2 ...] your message`"}), 200

        mention_str = " ".join(f"<@{uid}>" for uid in mentioned_ids)
        try:
            post_to_response_url(response_url, f"{mention_str} — {body}")
            return "", 200
        except Exception:
            log.exception("Failed to post announcement")
            return jsonify({"response_type": "ephemeral", "text": "Couldn’t post the announcement."}), 200

    # ---------- /ask ----------
    if command == "/ask":
        if not text:
            return jsonify({"response_type": "ephemeral", "text": "Usage: `/ask <prompt>`"}), 200

        def worker():
            answer = ask_gemini(text) or "(no answer)"
            message = f"<@{user_id}> asked: {text}\n\n*Gemini:* {answer}"
            try:
                post_to_response_url(response_url, message)
            except Exception:
                log.exception("Failed to post /ask response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    # ---------- /ask ----------
    if command == "/ask_rayhan":
        if not text:
            return jsonify({"response_type": "ephemeral", "text": "Usage: `/ask <prompt>`"}), 200

        def worker():
            answer = ask_gemini(text) or "(no answer)"
            message = f"<@{user_id}> asked: {text}\n\n*Gemini:* {answer}"
            try:
                post_to_response_url(response_url, message)
            except Exception:
                log.exception("Failed to post /ask response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    # ---------- /ask_test_danni ----------
    if command == "/ask_test_danni":
        if not text:
            return jsonify({"response_type": "ephemeral", "text": "Usage: `/ask <prompt>`"}), 200

        def worker():
            answer = ask_gemini(text) or "(no answer)"
            message = f"<@{user_id}> asked: {text}\n\n*Gemini:* {answer}"
            try:
                post_to_response_url(response_url, message)
            except Exception:
                log.exception("Failed to post /ask response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

     # ---------- /ask_test_emily ----------
    if command == "/ask_emily":
        if not text:
            return jsonify({"response_type": "ephemeral", "text": "Usage: `/ask <prompt>`"}), 200

        def worker():
            answer = ask_gemini(text) or "(no answer)"
            message = f"<@{user_id}> asked: {text}\n\n*Gemini:* {answer}"
            try:
                post_to_response_url(response_url, message)
            except Exception:
                log.exception("Failed to post /ask response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    # ---------- /opt_in ----------
    if command == "/opt_in":
        slack_id = request.form.get("user_id")
        user = users.get_user_by_slack_id(slack_id)
        if user:
            return jsonify({"text": "✅ You’re already opted in!"})
        # User not found → create
        user = users.create_user(slack_id)
        return jsonify({"text": f"🎉 You’ve successfully opted in! (UUID: {user.id})"})

    if command == "/generate_prompt":
        prompt_schema = {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string"
                }
            }
        }

        # Extract additional description from user input (everything after the command)
        additional_description = text.strip() if text.strip() else ""

        prompt = """You are a helpful event planning assistant that will generate a prompt that is a single, 
        open-ended question mean't to find common interest among users in a group.
        
        The question generated should be:
        - Open-ended, focused, and engaging (i.e. don't offer multiple follow-ups)
        - Suitable for group discussion
        - Designed to reveal common interests
        - Easy to answer with short responses
        - Does not ask for personal or potentiall sensative information

        Your goal: Generate a single creative question that will follow the above criteria. Please refer
        to the following groups description to help you curate the best question possible (if present):\n
        """

        # Get enterprise description
        enterprise = enterprises.get_enterprise_by_name(enterprise_name)
        if enterprise and enterprise.description:
            prompt += f"Group context: {enterprise.description}\n\n"
        else:
            prompt += "No group context available.\n\n"

        # Add user's additional description if provided
        if additional_description:
            prompt += f"Additional requirements from user: {additional_description}\n\n"

        prompt += "Please generate a single creative question based on the above information."

        if user_id and not users.is_user_admin(user_id):
            return jsonify({
                "response_type": "ephemeral",
                "text": "⚠️ You do not have permission to use this command."
            }), 200

        def worker():
            log.info("Generating prompt with Gemini Structured...")
            answer = ask_gemini_structured(
                prompt, prompt_schema) or "(no answer)"

            # Format the response message
            if additional_description:
                message = f"<@{user_id}> requested: {additional_description}\n\n*Generated prompt:* {answer.get('result', 'No answer generated')}"
            else:
                message = f"<@{user_id}> requested a prompt generation\n\n*Generated prompt:* {answer.get('result', 'No answer generated')}"

            # Save the generated prompt to the message bank
            if answer != "(no answer)" and answer.get('result'):
                messages.create_private_message(answer.get('result'))
                message += "\n\n✅ *Prompt saved to message bank!*"

            try:
                im_channel = open_im(user_id)
                chat_post_message(im_channel, message)
            except Exception:
                log.exception("Failed to post /generate_prompt response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    if command == "/set_enterprise_description":
        if user_id and not users.is_user_admin(user_id):
            return jsonify({
                "response_type": "ephemeral",
                "text": "⚠️ You do not have permission to use this command."
            }), 200

        def worker():
            if not enterprises.get_enterprise_by_name(enterprise_name):
                enterprises.create_enterprise(enterprise_name, text)
            else:
                enterprises.update_enterprise(enterprise_name, text)
            try:
                im_channel = open_im(user_id)
                chat_post_message(
                    im_channel, "Description of Slack group has been updated!")
            except Exception:
                log.exception("Failed to post /ask response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    if command == "/list_messages":
        if user_id and not users.is_user_admin(user_id):
            return jsonify({
                "response_type": "ephemeral",
                "text": "⚠️ You do not have permission to use this command."
            }), 200

        def worker():
            sys_messages = messages.get_orphaned_private_messages()

            # Format the messages for display
            if sys_messages:
                message_text = "📝 Available prompts:\n\n"
                for i, msg in enumerate(sys_messages, 1):
                    message_text += f"{i}. *ID: {msg.id}* - {msg.content}\n"

                message_text += "\n💡 *How to use a prompt:*\n"
                message_text += "• Use `/add_message_to_event <message_id> <event_id>` to associate a prompt with an event\n"
                message_text += "• Example: `/add_message_to_event 5 12` (associates message ID 5 with event ID 12)\n"
                message_text += "• Use `/list_events` to see available events"
            else:
                message_text = "📝 No available prompts found.\n\n"
                message_text += "💡 *How to add prompts:*\n"
                message_text += "• Use `/create_message <prompt_text>` to add a new prompt to the bank"

            try:
                im_channel = open_im(user_id)
                chat_post_message(im_channel, message_text)
            except Exception:
                log.exception("Failed to post /list_messages response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    # ---------- /opt_out ----------
    if command == "/opt_out":
        print("inside opt out function")
        slack_id = request.form.get("user_id")
        user = users.get_user_by_slack_id(slack_id)
        if user:
            # User found → delete
            deleted = users.delete_user(user.id)
            if deleted:
                return jsonify({"text": "👋 You've successfully opted out."})
        return jsonify({"text": "⚠️ You weren't opted in."})

    # ---------- /finalize_event ----------
    if command == "/finalize_event":
        """
        Finalize an event by grouping users and creating channels.
        Usage: /finalize_event [event_id]
        - If event_id is provided, finalize that specific event
        - If not provided, finalize the currently active event
        """
        def worker():
            try:
                # Parse event_id from text if provided
                target_event_id = None
                if text.strip():
                    try:
                        target_event_id = int(text.strip())
                        log.info(f"Finalizing event {target_event_id} (user-specified)")
                    except ValueError:
                        error_msg = f"⚠️ Invalid event ID: '{text}'. Please provide a number or leave blank for active event."
                        post_to_response_url(response_url, error_msg)
                        return
                
                # If no event_id provided, get the active event
                if target_event_id is None:
                    active_event = events.get_active_event()
                    if not active_event:
                        error_msg = "⚠️ No active event found. Please specify an event ID or create an event first."
                        post_to_response_url(response_url, error_msg)
                        return
                    target_event_id = active_event.id
                    log.info(f"Finalizing active event {target_event_id}")
                
                # Send immediate acknowledgment
                initial_msg = f"🔄 Finalizing event {target_event_id}... This may take a moment."
                post_to_response_url(response_url, initial_msg)
                
                # Call the event finalizer
                result = finalize_event(target_event_id)
                
                # Format response message
                if result["success"]:
                    message = f"✅ *Event {target_event_id} finalized successfully!*\n\n"
                    message += f"📊 *Summary:*\n"
                    message += f"• Groups created: {result['groups_created']}\n"
                    message += f"• Channels created: {len(result['channels_created'])}\n"
                    
                    if result['channels_created']:
                        message += f"\n📢 *Channels:*\n"
                        for channel_id in result['channels_created']:
                            message += f"• <#{channel_id}>\n"
                    
                    if result['errors']:
                        message += f"\n⚠️ *Warnings ({len(result['errors'])}):*\n"
                        for error in result['errors'][:3]:  # Show first 3 errors
                            message += f"• {error}\n"
                        if len(result['errors']) > 3:
                            message += f"• ... and {len(result['errors']) - 3} more\n"
                else:
                    message = f"❌ *Failed to finalize event {target_event_id}*\n\n"
                    if result['errors']:
                        message += f"*Errors:*\n"
                        for error in result['errors'][:5]:
                            message += f"• {error}\n"
                    else:
                        message += "No groups could be created from the responses."
                
                post_to_response_url(response_url, message)
                
            except Exception as e:
                log.error(f"Error in /finalize_event: {e}")
                error_msg = f"❌ Unexpected error: {str(e)}"
                try:
                    post_to_response_url(response_url, error_msg)
                except:
                    log.exception("Failed to post error response")
        
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    # Unknown command
    return jsonify({"response_type": "ephemeral", "text": f"Unsupported command: {command}"}), 200

    # TODO: Create groups
