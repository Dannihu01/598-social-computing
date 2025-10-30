#!/usr/bin/env python3
# --------------------------------------------------
# File: test_finalize_event.py
# Description: Test script for event finalization system
# --------------------------------------------------

import sys
import logging
from services.event_finalizer import finalize_event
from database.repos.events import get_active_event

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_finalize(event_id=None):
    """Test the event finalization system"""
    
    # If no event_id provided, use active event
    if event_id is None:
        active_event = get_active_event()
        if not active_event:
            print("❌ No active event found. Please create an event first or specify an event ID.")
            return
        event_id = active_event.id
        print(f"📋 Using active event: {event_id}")
    else:
        print(f"📋 Testing event: {event_id}")
    
    print(f"\n🔄 Starting finalization...\n")
    
    # Run finalization
    result = finalize_event(event_id)
    
    # Print results
    print("\n" + "="*60)
    print("FINALIZATION RESULTS")
    print("="*60)
    
    if result["success"]:
        print(f"✅ SUCCESS")
        print(f"\n📊 Summary:")
        print(f"   • Groups created: {result['groups_created']}")
        print(f"   • Channels created: {len(result['channels_created'])}")
        
        if result['channels_created']:
            print(f"\n📢 Channels:")
            for channel_id in result['channels_created']:
                print(f"   • {channel_id}")
        
        if result['errors']:
            print(f"\n⚠️  Warnings ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"   • {error}")
    else:
        print(f"❌ FAILED")
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"   • {error}")
        else:
            print("\n   No groups could be created from the responses.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            event_id = int(sys.argv[1])
            test_finalize(event_id)
        except ValueError:
            print(f"❌ Invalid event ID: '{sys.argv[1]}'. Please provide a number.")
            sys.exit(1)
    else:
        # No argument provided, use active event
        test_finalize()
