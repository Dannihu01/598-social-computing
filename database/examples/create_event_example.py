#!/usr/bin/env python3
"""
Example script showing how to create events using the database repository.
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# Add the project root directory to the path so we can import our modules
# This script is in database/examples/, so we need to go up 2 levels to reach project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from database.repos.events import create_event, delete_event
from database.db import init_pool, close_pool

def main():
    print("Creating events example...")
    print("=" * 50)
    
    # Initialize database connection
    # You'll need to replace this with your actual database connection string
    dsn = f"dbname={os.environ.get('DATABASE_NAME')} user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']} host={os.environ['DATABASE_HOST']} port={os.environ.get('DATABASE_PORT',5432)}"
    
    try:
        print("Initializing database connection...")
        
        init_pool(dsn)
        print("Database connection initialized!")
        
        # Example 1: Create an event that starts now and lasts 7 days (default)
        print("\n1. Creating event with default settings (starts now, 7 days duration):")
        result = create_event()
        print(f"Result: {result}")
        
        # Example 2: Create an event that starts in 1 hour and lasts 3 days
        print("\n2. Creating event that starts in 1 hour and lasts 3 days:")
        future_start = datetime.now() + timedelta(hours=1)
        result = create_event(time_start=future_start, day_duration=3)
        print(f"Result: {result}")
        
        # Example 3: Create an event that started yesterday and lasts 5 days
        print("\n3. Creating event that started yesterday and lasts 5 days:")
        past_start = datetime.now() - timedelta(days=1)
        result = create_event(time_start=past_start, day_duration=5)
        print(f"Result: {result}")
        
        print("\n" + "=" * 50)
        print("Event creation examples completed!")
        
        # Example 4: Delete an event (using a made-up ID for demonstration)
        print("\n4. Attempting to delete event with ID 999 (should fail):")
        result = delete_event(999)
        print(f"Result: {result}")
        
        print("\n" + "=" * 50)
        print("Event deletion example completed!")
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Please make sure PostgreSQL is running and update the DSN string.")
        return
    finally:
        # Clean up database connection
        print("\nClosing database connection...")
        close_pool()

if __name__ == "__main__":
    main()
