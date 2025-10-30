
from typing import List, Tuple


def get_classification_prompt(responses: List[Tuple[str, str]]) -> str:
    """
    Generate prompt for classifying users into groups based on response similarity.
    
    Args:
        responses: List of (slack_id, response_text) tuples
        
    Returns:
        Formatted prompt string for Gemini
    """
    formatted_responses = "\n".join([
        f"User {slack_id}: {entry}" 
        for slack_id, entry in responses
    ])
    
    prompt = f"""Analyze these user responses and group users with similar content and sentiment together.

Responses:
{formatted_responses}

Requirements:
- Minimum group size: 2 users
- No maximum group size
- Users with unique/dissimilar responses can be left ungrouped (don't force them into groups)
- Focus on thematic similarity, shared interests, and sentiment alignment
- Group users who would benefit from connecting based on their responses

Return ONLY a JSON array of groups, where each group is an array of user slack_ids (the strings starting with "U").
Example format: [["U123ABC", "U456DEF"], ["U789GHI", "U012JKL"]]

Only include groups with 2 or more users. Do not include single-user groups.
"""
    
    return prompt


def get_channel_metadata_prompt(user_responses: List[Tuple[str, str]]) -> str:
    """
    Generate prompt for creating channel metadata based on grouped user responses.
    
    Args:
        user_responses: List of (slack_id, response_text) tuples for a single group
        
    Returns:
        Formatted prompt string for Gemini
    """
    formatted_responses = "\n".join([
        f"- {entry}" for _, entry in user_responses
    ])
    
    slack_ids = [slack_id for slack_id, _ in user_responses]
    mentions = ", ".join(slack_ids)
    
    prompt = f"""Based on these similar user interests, create metadata for a Slack channel to connect them:

User Responses:
{formatted_responses}

Users to be added: {mentions}

Generate the following:
1. channel_name: A short, descriptive Slack channel name (lowercase, use hyphens instead of spaces, max 80 characters, no special characters except hyphens)
2. initial_message: A warm welcome message explaining why these users were grouped together (2-3 sentences, be specific about their shared interests)
3. call_to_action: An engaging question or prompt to help them start the conversation (1 sentence)

Return as JSON with exactly these keys: channel_name, initial_message, call_to_action
"""
    
    return prompt
