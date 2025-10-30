# --------------------------------------------------
# File: services/channel_generator.py
# Description: Generate channel metadata using Gemini
# --------------------------------------------------

import logging
from typing import Dict, List, Tuple, Optional
from services.gemini_client import ask_gemini_structured
from prompts.event_prompts import get_channel_metadata_prompt
from schemas.gemini_schemas import CHANNEL_METADATA_SCHEMA

log = logging.getLogger("channel-generator")


def generate_channel_metadata(user_responses: List[Tuple[str, str]]) -> Optional[Dict[str, str]]:
    """
    Generate channel name, welcome message, and call-to-action using Gemini.
    
    Args:
        user_responses: List of (slack_id, response_text) tuples
        
    Returns:
        Dict with keys: channel_name, initial_message, call_to_action
        Returns None if generation fails
    """
    try:
        if not user_responses:
            log.warning("Cannot generate metadata for empty user_responses")
            return None
        
        log.info(f"Generating channel metadata for {len(user_responses)} users")
        
        # Generate prompt
        prompt = get_channel_metadata_prompt(user_responses)
        
        # Call Gemini with structured output
        metadata = ask_gemini_structured(
            prompt,
            schema=CHANNEL_METADATA_SCHEMA,
            mime_type="application/json"
        )
        
        if not metadata:
            log.warning("Gemini returned empty metadata")
            return None
        
        # Validate and sanitize channel name
        channel_name = metadata.get("channel_name", "").lower()
        # Replace any non-alphanumeric (except hyphen) with hyphen
        channel_name = "".join(c if c.isalnum() or c == '-' else '-' for c in channel_name)
        # Remove consecutive hyphens
        while '--' in channel_name:
            channel_name = channel_name.replace('--', '-')
        # Trim and limit to 80 chars
        channel_name = channel_name.strip('-')[:80]
        
        if not channel_name:
            log.warning("Generated channel name is empty after sanitization")
            return None
        
        metadata["channel_name"] = channel_name
        
        log.info(f"Generated metadata for channel: {channel_name}")
        return metadata
    
    except Exception as e:
        log.error(f"Failed to generate channel metadata: {e}")
        return None
