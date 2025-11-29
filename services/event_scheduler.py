# --------------------------------------------------
# File: services/event_scheduler.py
# Description: Background scheduler to auto-finalize events when they end
# --------------------------------------------------

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database.repos.events import get_unfinalized_ended_events, mark_event_finalized
from database.repos.responses import get_responses_with_users
from services.event_finalizer import finalize_event

log = logging.getLogger("event-scheduler")

scheduler = None


def check_and_finalize_events():
    """
    Check if any events have ended and need auto-finalization.
    This runs periodically in the background.
    """
    try:
        log.info("Checking for events to finalize...")
        
        # Get all events that have ended but haven't been finalized yet
        ended_events = get_unfinalized_ended_events()
        
        if not ended_events:
            log.info("No unfinalized ended events found")
            return
        
        log.info(f"Found {len(ended_events)} ended event(s) to process")
        
        # Process each ended event
        for event in ended_events:
            event_id = event.id
            log.info(f"Processing event {event_id}")
            
            # Check if there are enough responses
            responses = get_responses_with_users(event_id)
            if not responses or len(responses) < 2:
                log.info(f"Event {event_id} has {len(responses) if responses else 0} responses (need at least 2), skipping finalization")
                # Mark as finalized anyway so we don't keep checking it
                mark_event_finalized(event_id)
                continue
            
            log.info(f"Auto-finalizing event {event_id} with {len(responses)} responses...")
            
            # Run finalization
            result = finalize_event(event_id)
            
            if result["success"]:
                log.info(f"✅ Event {event_id} auto-finalized successfully! "
                        f"Created {len(result['channels_created'])} channels")
                # Mark event as finalized
                mark_event_finalized(event_id)
            else:
                log.warning(f"⚠️ Event {event_id} finalization completed with errors: {result['errors']}")
                # Still mark as finalized to prevent retrying
                mark_event_finalized(event_id)
    
    except Exception as e:
        log.error(f"Error in auto-finalization check: {e}", exc_info=True)


def start_scheduler(check_interval_minutes=5):
    """
    Start the background scheduler to check for events to finalize.
    
    Args:
        check_interval_minutes: How often to check (default: 5 minutes)
    """
    global scheduler
    
    if scheduler is not None:
        log.warning("Scheduler already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule the check to run every X minutes
    scheduler.add_job(
        check_and_finalize_events,
        'interval',
        minutes=check_interval_minutes,
        id='auto_finalize_events',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )
    
    # Also run once at startup (after a short delay)
    scheduler.add_job(
        check_and_finalize_events,
        'date',
        run_date=datetime.now(),
        id='startup_check',
        misfire_grace_time=60
    )
    
    scheduler.start()
    log.info(f"✅ Event scheduler started! Checking every {check_interval_minutes} minutes")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        log.info("Event scheduler stopped")
