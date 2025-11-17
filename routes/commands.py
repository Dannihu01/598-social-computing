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

from utils.slack_api import open_im, chat_post_message
from services.gemini_client import ask_gemini_structured
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from database.repos import users, enterprises, messages, events, responses, events
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
    enterprise_name = request.form.get(
        "enterprise_name", None) or request.form.get("team_domain", "default")
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

        def worker():
            user = users.get_user_by_slack_id(slack_id)
            message = [
                f"🎉 You’ve successfully opted in!\n ",
                "Terms of Service: By opting-in, you are agreeing to participating in a term-project for Social Computing, ",
                "CSE 598-012. We only collect responses you provide, which are used with LLMs to generate new channels. If at any point you wish to not ",
                "participate, please use the command '/opt_out'. To review this message, simply type '/opt_in'. Thank you for joining us!"
            ]
            message = "/n".join(message)
            if not user:
                user = users.create_user(slack_id)
            im_channel = open_im(slack_id)
            chat_post_message(im_channel, message)

        return jsonify({
            "response_type": "ephemeral",
            "text": f"Processing opt-in, you should receieve a confirmation DM once you are registered."
        }), 200

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
        open-ended question meant to find common interest among users in a group.
        
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
        print(f"ENTERPRISE NAME: {enterprise_name}")
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

    # inside routes/commands.py, in the POST /slack/commands handler:

    if command == "/reset_event_number":
        events.reset_event_counter()
        return jsonify({"text": "✅ Event counter reset to 1."}), 200

    # ---------- /start_event ----------
    if command == "/start_event":
        """
        Usage: /start_event [duration_in_days]
        Examples:
            /start_event        (default: 3 days)
            /start_event 5     (5 days)
        """
        try:
            # Parse duration from text (default: 60 days)
            duration_days = 3
            if text.strip():
                try:
                    duration_days = int(text.strip())
                    if duration_days <= 0:
                        return jsonify({
                            "response_type": "ephemeral",
                            "text": "⚠️ Duration must be a positive number of days."
                        }), 200
                except ValueError:
                    return jsonify({
                        "response_type": "ephemeral",
                        "text": "⚠️ Invalid duration. Usage: `/start_event [duration_in_days]`\nExample: `/start_event 3` for 3 days"
                    }), 200

            # create new event
            time_start = datetime.now(tz=ZoneInfo(
                "America/New_York")).replace(microsecond=0)
            result = events.create_event(
                time_start=time_start, duration_days=duration_days)

            if result == "event_already_active":
                return jsonify({"response_type": "ephemeral", "text": "⚠️ There is already an active event."}), 200
            if result != "success":
                return jsonify({"response_type": "ephemeral", "text": "❌ Couldn't create event."}), 200

            # Fetch the event we just created
            evt = events.get_active_event()

            # Get an unused prompt (not used in any unfinalized events)
            unused_msgs = messages.get_unused_private_messages()
            if not unused_msgs:
                return jsonify({"response_type": "ephemeral", "text": "⚠️ No unused prompts found. All prompts are currently in use, or add more with `/create_message <text>`."}), 200
            # Get first unused prompt (already randomized in query)
            msg = unused_msgs[0]

            # Attach prompt to event
            events.add_message_to_event(evt.id, msg.id)

            # Calculate end time for DM message
            end_time = time_start + timedelta(days=duration_days)

            # Format duration for user-friendly display
            time_remaining = f"{duration_days} days"

            # Create the full message with prompt and time information
            dm_message = f"{msg.content}\n\n" \
                f"⏰ *Time to respond:* {time_remaining}\n" \
                f"📅 *Response deadline:* {end_time.strftime('%I:%M %p %Z, %b %d')}"

            # DM all opted-in users
            delivered = failed = 0
            for u in users.list_users(limit=100000):
                print()
                print(u)
                slack_id = getattr(u, "slack_id", None)
                if not slack_id:
                    continue
                try:
                    dm = open_im(slack_id)
                    if isinstance(dm, dict) and "channel" in dm:
                        dm = dm["channel"]["id"]
                    chat_post_message(dm, dm_message)
                    delivered += 1
                except Exception as e:
                    log.error(f"Failed to DM {slack_id}: {e}")
                    failed += 1

            # Format duration for admin confirmation display
            duration_display = f"{duration_days} day(s)"

            return jsonify({"response_type": "ephemeral",
                            "text": f"✅ Started event {evt.id} with prompt {msg.id}\n"
                            f"⏱️ Duration: {duration_display}\n"
                            f"📅 Ends at: {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                            f"📨 DMs sent: {delivered}, failed: {failed}"}), 200

        except Exception:
            log.exception("start_event failed")
            return jsonify({"response_type": "ephemeral", "text": "❌ Couldn't start event. Check logs."}), 200

    # ---------- /send_survey ----------
    if command == "/send_survey":
        '''
        Usage: /send_survey <survey_url>
        '''
        survey_url = request.form.get("text")

        # get current event and list of responders
        current_event = events.get_active_event()
        print("Current event:", current_event)
        responder_user_ids = responses.get_event_user_ids(current_event.id)
        print(f"Responses for event {current_event.id}:", responder_user_ids)

        if not responder_user_ids:
            return jsonify({"text": f"No one responded."}), 200

        msg = f"Thanks for responding to our last question! Please fill out this quick survey so we can hear your thoughts: {survey_url}"

        success, failed = [], []

        for r in responder_user_ids:
            try:
                # get Slack ID for the user
                user = users.get_user_by_id(r)
                slack_id = user.slack_id if hasattr(user, "slack_id") else user
                print("slack id:", slack_id)

                print(f"Opening DM with user {slack_id}")
                dm_channel = open_im(slack_id)
                print(f"DM channel opened: {dm_channel}")

                print(f"Sending message to channel {dm_channel}: '{msg}'")
                chat_post_message(dm_channel, msg)
                print(f"Message sent successfully to <@{slack_id}>")

                success.append(slack_id)

            except Exception as e:
                log.error(f"Error sending DM to {slack_id}: {e}")
                failed.append(slack_id)

        print(f"DMs sent to {len(success)} users, failed for {len(failed)}")
        return jsonify({"text": f"Sent survey to {len(success)} users, failed for {len(failed)}"}), 200

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
                        log.info(
                            f"Finalizing event {target_event_id} (user-specified)")
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
