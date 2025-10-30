# --------------------------------------------------
# File: schemas/gemini_schemas.py
# Description: JSON schemas for Gemini structured outputs
# --------------------------------------------------

CLASSIFICATION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "array",
        "items": {"type": "string"}
    },
    "description": "Array of user groups, each group is an array of user slack_ids"
}

CHANNEL_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "channel_name": {
            "type": "string",
            "description": "Slack-compatible channel name (lowercase, hyphens, max 80 chars)"
        },
        "initial_message": {
            "type": "string",
            "description": "Welcome message explaining why these users were grouped (2-3 sentences)"
        },
        "call_to_action": {
            "type": "string",
            "description": "Engaging question or prompt to start conversation (1 sentence)"
        }
    },
    "required": ["channel_name", "initial_message", "call_to_action"]
}
