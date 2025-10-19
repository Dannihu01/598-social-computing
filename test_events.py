#!/usr/bin/env python3
"""
Simple test script for event functions.
Run this from the project root directory.
"""

from database.repos.events import create_event, delete_event, is_event_over
from datetime import datetime, timedelta

def test_events():
    print("Testing event functions...")
    print("=" * 50)
    
    # Test 1: Create an event
    print("\n1. Creating a test event...")
    result = create_event(day_duration=1)  # 1 day duration for quick testing
    print(f"Create result: {result}")
    
    # Test 2: Create another event that's already over
    print("\n2. Creating an event that's already over...")
    past_start = datetime.now() - timedelta(days=2)  # Started 2 days ago
    result = create_event(time_start=past_start, day_duration=1)  # Only 1 day duration
    print(f"Create result: {result}")
    
    # Test 3: Check if events are over (we'll use event ID 1 and 2)
    print("\n3. Checking if events are over...")
    for event_id in [1, 2]:
        is_over = is_event_over(event_id)
        print(f"Event {event_id} is over: {is_over}")
    
    # Test 4: Try to delete a non-existent event
    print("\n4. Trying to delete non-existent event...")
    result = delete_event(999)
    print(f"Delete result: {result}")
    
    print("\n" + "=" * 50)
    print("Event testing completed!")

if __name__ == "__main__":
    test_events()
