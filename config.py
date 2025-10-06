# config.py
import os
from dotenv import load_dotenv
load_dotenv()

PORT = int(os.environ.get("PORT", 8080))

# Slack
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]   # set in Render
SLACK_BOT_TOKEN      = os.environ.get("SLACK_BOT_TOKEN")     # xoxb-..., required for /dm

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_USE_REST = os.environ.get("GEMINI_USE_REST", "0") == "1"
