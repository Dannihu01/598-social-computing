import logging
from flask import Blueprint, request, redirect, url_for, jsonify
import requests
from utils.verify import verify_slack
from services.thread_monitor import process_message_event, process_reaction_event
from dotenv import load_dotenv
import os
load_dotenv()
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

log = logging.getLogger("slack-ask-bot")
oauth_bp = Blueprint("oauth_bp", __name__, url_prefix="/slack")

@oauth_bp.get("/oauth/callback")
def oauth_callback():
    # Slack redirects here after user approves
    code = request.args.get('code')
    state = request.args.get('state')
    # redirect_uri = url_for('oauth_bp.oauth_callback', _external=True)
    redirect_uri = "https://lexicographic-shanika-tightknit.ngrok-free.dev/slack/oauth/callback"
    print("Redirect URI:", redirect_uri)

    # Exchange the code for an access token
    token_response = requests.post(
        'https://slack.com/api/oauth.v2.access',
        data={
            'code': code,
            'client_id': SLACK_CLIENT_ID,
            'client_secret': SLACK_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
        }
    )
    data = token_response.json()
    if data.get('ok'):
        bot_token = data.get('access_token')
        refresh_token = data.get('refresh_token')  # present if token rotation enabled
        os.environ['SLACK_BOT_TOKEN'] = bot_token
        if refresh_token:
            os.environ['SLACK_REFRESH_TOKEN'] = refresh_token
        log.info("Stored Slack bot token from OAuth callback. Refresh token present: %s", bool(refresh_token))
        return data, 200
    else:
        log.error("Slack OAuth token exchange failed: %s", data)
        return jsonify({'status': 'failure', 'error': data}), 500