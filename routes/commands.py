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
from services.gemini_client import ask_gemini

from database.repos import responses, users
log = logging.getLogger("slack-ask-bot")
commands_bp = Blueprint("commands_bp", __name__, url_prefix="/slack")


@commands_bp.post("/commands")
def slash():
    print("made it here")
    if not verify_slack(request):
        return "invalid signature", 401

    command = request.form.get("command", "")
    user_id = request.form.get("user_id", "")
    channel_id = request.form.get("channel_id", "")
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

    # ---------- /Jakob's testing command ----------
    if command == "/jakob_test":
        if not text:
            return jsonify({"response_type": "ephemeral", "text": "Usage: `/ask <prompt>`"}), 200

        def worker():
            # user = users.create_user("U12345")
            responses_list = responses.get_event_responses(1)
            # message = f"<@{user_id}> asked: {text}\n\n*Gemini:* {answer}"
            try:
                post_to_response_url(response_url, str(responses_list))
            except Exception:
                log.exception("Failed to post /ask response")
        threading.Thread(target=worker, daemon=True).start()
        return "", 200

    # Unknown command
    return jsonify({"response_type": "ephemeral", "text": f"Unsupported command: {command}"}), 200

    # TODO: Create groups
