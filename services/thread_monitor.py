import logging
from typing import List, Dict
from datetime import datetime
from database.db import get_conn, put_conn
from database.repos.users import get_user_by_slack_id, create_user
from services.gemini_client import ask_gemini_structured
from utils.slack_api import open_im, chat_post_message, slack_api

log = logging.getLogger("thread-monitor")

def process_message_event(event: Dict):
    """Process a message event in a thread"""
    thread_ts = event.get("thread_ts")
    channel_id = event.get("channel")
    user_slack_id = event.get("user")
    message_text = event.get("text", "")
    message_ts = event.get("ts")
    # Ensure user exists in DB
    user = get_user_by_slack_id(user_slack_id)
    if not user:
        user = create_user(user_slack_id)
    
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Upsert monitored_thread
            cur.execute("""
                INSERT INTO monitored_threads (thread_ts, channel_id, last_activity, message_count, original_message)
                VALUES (%s, %s, NOW(), 1, %s)
                ON CONFLICT (thread_ts) DO UPDATE
                SET last_activity = NOW(),
                    message_count = monitored_threads.message_count + 1
            """, (thread_ts, channel_id, message_text if event.get("ts") == thread_ts else None))
            
            # Upsert thread participant
            cur.execute("""
                INSERT INTO thread_participants (thread_ts, user_id, slack_id, message_count, last_engaged, engagement_score)
                VALUES (%s, %s, %s, 1, NOW(), 10)
                ON CONFLICT (thread_ts, user_id) DO UPDATE
                SET message_count = thread_participants.message_count + 1,
                    last_engaged = NOW(),
                    engagement_score = thread_participants.engagement_score + 10
            """, (thread_ts, user.uuid, user_slack_id))
            
            conn.commit()
            
            # Check if intervention criteria met
            check_and_intervene(thread_ts, channel_id)
    finally:
        put_conn(conn)

def process_reaction_event(event: Dict):
    """Process a reaction as engagement signal"""
    item = event.get("item", {})
    thread_ts = item.get("ts")  # Could be thread_ts or message ts
    channel_id = event.get("item", {}).get("channel")
    user_slack_id = event.get("user")
    
    # Ensure user exists
    user = get_user_by_slack_id(user_slack_id)
    if not user:
        user = create_user(user_slack_id)
    
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # ENSURE THREAD EXISTS FIRST (same as in process_message_event)
            cur.execute("""
                INSERT INTO monitored_threads (thread_ts, channel_id, last_activity, message_count)
                VALUES (%s, %s, NOW(), 0)
                ON CONFLICT (thread_ts) DO UPDATE
                SET last_activity = NOW()
            """, (thread_ts, channel_id))
            
            # Update participant engagement
            cur.execute("""
                INSERT INTO thread_participants (thread_ts, user_id, slack_id, reaction_count, last_engaged, engagement_score)
                VALUES (%s, %s, %s, 1, NOW(), 5)
                ON CONFLICT (thread_ts, user_id) DO UPDATE
                SET reaction_count = thread_participants.reaction_count + 1,
                    last_engaged = NOW(),
                    engagement_score = thread_participants.engagement_score + 5
            """, (thread_ts, user.uuid, user_slack_id))
            
            conn.commit()
            
            check_and_intervene(thread_ts, channel_id)
    finally:
        put_conn(conn)

        
def check_and_intervene(thread_ts: str, channel_id: str):
    """Check if intervention criteria met and take action"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Get thread info
            cur.execute("""
                SELECT bot_intervened, intervention_type, message_count 
                FROM monitored_threads 
                WHERE thread_ts = %s
            """, (thread_ts,))
            thread_row = cur.fetchone()
            
            if not thread_row:
                return
            
            bot_intervened = thread_row[0]
            current_intervention = thread_row[1]
            
            # Get engaged participants (sorted by engagement score)
            cur.execute("""
                SELECT user_id, slack_id, engagement_score
                FROM thread_participants
                WHERE thread_ts = %s AND engagement_score >= 10
                ORDER BY engagement_score DESC
            """, (thread_ts,))
            participants = cur.fetchall()
            
            num_engaged = len(participants)
            
            # PROGRESSIVE INTERVENTION LOGIC
            # Allow escalation: dm_pair → ephemeral → create_channel
            
            if num_engaged >= 4 and current_intervention != 'create_channel':
                # Upgrade to channel creation (highest intervention)
                create_group_channel(thread_ts, channel_id, participants, cur, conn)
            
            elif num_engaged == 3 and current_intervention not in ['ephemeral', 'create_channel']:
                # Upgrade to ephemeral (medium intervention)
                create_group_channel(thread_ts, channel_id, participants, cur, conn)
                            
            elif num_engaged == 2 and not bot_intervened:
                # Initial intervention: DM pair (lowest intervention)
                send_dm_to_pair(thread_ts, channel_id, participants[:2], cur, conn)
    
    finally:
        put_conn(conn)

def send_dm_to_pair(thread_ts: str, channel_id: str, participants: List, cur, conn):
    """Send DM to 2 interested people suggesting they connect"""
    user1_slack_id = participants[0][1]
    user2_slack_id = participants[1][1]
    
    try:
        # DM to user 1
        dm1 = open_im(user1_slack_id)
        chat_post_message(
            dm1, 
            f"👋 I noticed you and <@{user2_slack_id}> are both engaged in a discussion. Want to connect and chat more?"
        )
        
        # DM to user 2
        dm2 = open_im(user2_slack_id)
        chat_post_message(
            dm2,
            f"👋 I noticed you and <@{user1_slack_id}> are both engaged in a discussion. Want to connect and chat more?"
        )
        
        # Log intervention
        cur.execute("""
            INSERT INTO bot_interventions (source_thread_ts, intervention_type, target_slack_ids, successful)
            VALUES (%s, 'dm_pair', %s, TRUE)
        """, (thread_ts, [user1_slack_id, user2_slack_id]))
        
        # Mark thread as intervened
        cur.execute("""
            UPDATE monitored_threads SET bot_intervened = TRUE, intervention_type = 'dm_pair'
            WHERE thread_ts = %s
        """, (thread_ts,))
        
        conn.commit()
        log.info(f"Sent DM pair intervention for thread {thread_ts}")
    
    except Exception as e:
        log.error(f"Failed to send DM pair: {e}")

def create_group_channel(thread_ts: str, channel_id: str, participants: List, cur, conn):
    """Create a new Slack channel for 4+ interested people"""
    slack_ids = [p[1] for p in participants[:8]]  # Limit to top 8 most engaged
    
    try:
        # Analyze thread topic using Gemini
        topic = analyze_thread_topic(thread_ts, channel_id)
        
        # Create channel name (Slack max 80 chars, lowercase, no spaces)
        channel_name = f"discussion-{topic[:30].lower().replace(' ', '-')}-{thread_ts[-6:]}"
        
        # Create the channel
        result = slack_api("conversations.create", {
            "name": channel_name,
            "is_private": False
        })
        new_channel_id = result["channel"]["id"]
        
        # Invite participants
        slack_api("conversations.invite", {
            "channel": new_channel_id,
            "users": ",".join(slack_ids)
        })
        
        # Post initial message
        mentions = " ".join([f"<@{sid}>" for sid in slack_ids])
        chat_post_message(
            new_channel_id,
            f"👋 {mentions}\n\nI noticed you all engaged in a discussion about **{topic}**. "
            f"This channel was created for you to continue the conversation!"
        )
        
        # Log intervention
        cur.execute("""
            INSERT INTO bot_interventions (source_thread_ts, intervention_type, target_slack_ids, channel_id, successful)
            VALUES (%s, 'create_channel', %s, %s, TRUE)
        """, (thread_ts, slack_ids, new_channel_id))
        
        # Mark thread as intervened
        cur.execute("""
            UPDATE monitored_threads SET bot_intervened = TRUE, intervention_type = 'create_channel'
            WHERE thread_ts = %s
        """, (thread_ts,))
        
        conn.commit()
        log.info(f"Created channel {channel_name} for thread {thread_ts}")
    
    except Exception as e:
        log.error(f"Failed to create channel: {e}")

def send_ephemeral_to_group(thread_ts: str, channel_id: str, participants: List, cur, conn):
    """Send ephemeral message to 3 people in the original channel"""
    slack_ids = [p[1] for p in participants]
    
    try:
        for slack_id in slack_ids:
            slack_api("chat.postEphemeral", {
                "channel": channel_id,
                "user": slack_id,
                "thread_ts": thread_ts,
                "text": "👋 I noticed you're engaged in this discussion. If one more person joins, I can create a dedicated channel for this topic!"
            })
        
        log.info(f"Sent ephemeral messages for thread {thread_ts}")
    except Exception as e:
        log.error(f"Failed to send ephemeral: {e}")

def analyze_thread_topic(thread_ts: str, channel_id: str) -> str:
    """Use Gemini to analyze thread and extract topic"""
    try:
        # Fetch thread messages via Slack API
        result = slack_api("conversations.replies", {
            "channel": channel_id,
            "ts": thread_ts,
            "limit": 10
        })
        messages = result.get("messages", [])
        thread_text = "\n".join([msg.get("text", "") for msg in messages[:5]])
        
        # Ask Gemini for topic
        topic = ask_gemini_structured(
            f"Analyze this Slack thread and extract the main topic in 2-4 words:\n\n{thread_text}",
            schema={"type": "object", "properties": {"topic": {"type": "string"}}},
            mime_type="application/json"
        )
        return topic.get("topic", "discussion") if topic else "discussion"
    except:
        return "discussion"