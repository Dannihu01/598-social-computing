# --------------------------------------------------
# File: services/response_classifier.py
# Description: Classify user responses into groups using Gemini
# --------------------------------------------------

import logging
from typing import List, Optional
from database.repos.responses import get_responses_with_users
from services.gemini_client import ask_gemini_structured
from prompts.event_prompts import get_classification_prompt
from schemas.gemini_schemas import CLASSIFICATION_SCHEMA

log = logging.getLogger("response-classifier")


def classify_user_responses(event_id: int) -> Optional[List[List[str]]]:
    """
    Classify users into groups based on response similarity.
    
    Args:
        event_id: The event ID to fetch responses for
        
    Returns:
        List of groups, each containing list of user slack_ids
        Example: [['U123', 'U456'], ['U789', 'U012']]
        Returns None if classification fails or not enough responses
    """
    try:
        # Get responses with user info from database
        responses = get_responses_with_users(event_id)
        
        if len(responses) < 2:
            log.info(f"Not enough responses for event {event_id} (found {len(responses)})")
            return None
        
        log.info(f"Classifying {len(responses)} responses for event {event_id}")
        
        # Generate prompt
        prompt = get_classification_prompt(responses)
        
        # Call Gemini with structured output
        groups = ask_gemini_structured(
            prompt, 
            schema=CLASSIFICATION_SCHEMA, 
            mime_type="application/json"
        )
        
        if not groups:
            log.warning(f"Gemini returned empty groups for event {event_id}")
            return None
        
        # Filter out groups with < 2 members (enforce minimum)
        valid_groups = [g for g in groups if isinstance(g, list) and len(g) >= 2]
        
        log.info(f"Classified into {len(valid_groups)} valid groups (from {len(groups)} total)")
        return valid_groups
    
    except Exception as e:
        log.error(f"Failed to classify responses for event {event_id}: {e}")
        return None
