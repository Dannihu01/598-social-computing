# --------------------------------------------------
# File: app.py
# Description: Initializes the Flask application, sets up logging,
# and registers the Slack command routes for the Slack Ask Bot service.
# --------------------------------------------------

import logging
import atexit
from flask import Flask, jsonify
from config import PORT
from routes.commands import commands_bp
from routes.events import events_bp
from routes.oauth import oauth_bp
import os
from database import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("slack-ask-bot")

app = Flask(__name__)
app.register_blueprint(commands_bp)  # mounts /slack/commands
app.register_blueprint(events_bp)  # mounts /slack/events
app.register_blueprint(oauth_bp)  # mounts /slack/oauth/callback


# DB access
# initialize DB
dsn = f"dbname={os.environ.get('DATABASE_NAME')} user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']} host={os.environ['DATABASE_HOST']} port={os.environ.get('DATABASE_PORT',5432)}"
db.init_pool(dsn=dsn)

# Register cleanup function to close DB pool on app shutdown
atexit.register(db.close_pool)


@app.get("/")
def root():
    return jsonify({"ok": True, "service": "slack-ask-bot"}), 200


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=PORT, debug=True)
    finally:
        # Ensure DB pool is closed on exit
        db.close_pool()
