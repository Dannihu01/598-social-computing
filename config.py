# --------------------------------------------------
# File: config.py
# Description: Loads environment variables and configuration settings
# for the Slack Ask Bot, including server port, Slack credentials,
# and Gemini API parameters.
# --------------------------------------------------
from database import db
from dotenv import load_dotenv
import os

load_dotenv()

PORT = int(os.environ.get("PORT", 8080))

# Slack
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]   # set in Render
SLACK_BOT_TOKEN = os.environ.get(
    "SLACK_BOT_TOKEN")     # xoxb-..., required for /dm

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_USE_REST = os.environ.get("GEMINI_USE_REST", "0") == "1"

# Event Scheduler
# How often to check for events to finalize (in minutes)
EVENT_FINALIZATION_CHECK_INTERVAL = int(os.environ.get("EVENT_FINALIZATION_CHECK_INTERVAL", 5))
