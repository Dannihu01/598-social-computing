# Add this to your Slack App Manifest

## In the "slash_commands" section, add:

```json
{
    "command": "/finalize_event",
    "url": "https://your-ngrok-url.ngrok.io/slack/commands",
    "description": "Finalize event by grouping users and creating channels",
    "usage_hint": "[event_id] (optional, defaults to active event)",
    "should_escape": false
}
```

## Required Bot Scopes (verify these exist):

```json
{
    "oauth_config": {
        "scopes": {
            "bot": [
                "channels:read",
                "channels:manage",      // For creating channels
                "channels:history",
                "chat:write",
                "commands",
                "groups:read",
                "groups:history",
                "groups:write",
                "im:write",
                "im:history",
                "reactions:read"
            ]
        }
    }
}
```

## Full Command Example for Manifest:

If you're using ngrok locally:
```json
{
    "command": "/finalize_event",
    "url": "https://predark-justly-johan.ngrok-free.dev/slack/commands",
    "description": "Finalize event by grouping users and creating channels",
    "usage_hint": "[event_id]",
    "should_escape": false
}
```

If deployed on Render:
```json
{
    "command": "/finalize_event",
    "url": "https://five98-social-computing-bot.onrender.com/slack/commands",
    "description": "Finalize event by grouping users and creating channels",
    "usage_hint": "[event_id]",
    "should_escape": false
}
```

## After Adding to Manifest:

1. Save the manifest in Slack app settings
2. Reinstall the app to your workspace (OAuth & Permissions → Reinstall App)
3. Test the command: `/finalize_event`
