# app.py
import logging
from flask import Flask, jsonify
from config import PORT
from routes.commands import commands_bp

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("slack-ask-bot")

app = Flask(__name__)
app.register_blueprint(commands_bp)  # mounts /slack/commands

@app.get("/")
def root():
    return jsonify({"ok": True, "service": "slack-ask-bot"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

