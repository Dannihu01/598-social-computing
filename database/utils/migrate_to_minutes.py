#!/usr/bin/env python3
"""
Migration script to convert events table from day_duration to duration_minutes
Run this once to update your database schema.
"""

import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Run the migration to convert day_duration to duration_minutes"""
    
    print("=" * 60)
    print("MIGRATION: Convert events.day_duration to events.duration_minutes")
    print("=" * 60)
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.environ.get("DATABASE_HOST"),
        user=os.environ.get("DATABASE_USER"),
        password=os.environ.get("DATABASE_PASSWORD"),
        port=os.environ.get("DATABASE_PORT"),
        database=os.environ.get("DATABASE_NAME"),
        connect_timeout=10
    )
    
    try:
        cursor = conn.cursor()
        
        # Check if day_duration column still exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'events' AND column_name = 'day_duration'
        """)
        
        if not cursor.fetchone():
            print("✅ Migration already complete! duration_minutes column exists.")
            print("\nChecking current schema...")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'events' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("\nCurrent events table columns:")
            for col in columns:
                print(f"  • {col[0]} ({col[1]})")
            return
        
        print("\n📋 Steps:")
        print("1. Add duration_minutes column")
        print("2. Convert existing data (days → minutes)")
        print("3. Drop day_duration column")
        print("4. Set default value")
        
        input("\nPress Enter to continue or Ctrl+C to cancel...")
        
        # Step 1: Add new column
        print("\n➡️  Adding duration_minutes column...")
        cursor.execute("ALTER TABLE events ADD COLUMN duration_minutes INTEGER")
        conn.commit()
        print("✅ Column added")
        
        # Step 2: Convert existing data
        print("\n➡️  Converting existing data...")
        cursor.execute("""
            UPDATE events 
            SET duration_minutes = day_duration * 1440 
            WHERE day_duration IS NOT NULL
        """)
        rows_updated = cursor.rowcount
        conn.commit()
        print(f"✅ Updated {rows_updated} events")
        
        # Step 3: Drop old column
        print("\n➡️  Dropping day_duration column...")
        cursor.execute("ALTER TABLE events DROP COLUMN day_duration")
        conn.commit()
        print("✅ Column dropped")
        
        # Step 4: Set default
        print("\n➡️  Setting default value (60 minutes)...")
        cursor.execute("ALTER TABLE events ALTER COLUMN duration_minutes SET DEFAULT 60")
        conn.commit()
        print("✅ Default set")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  • Converted {rows_updated} existing events")
        print("  • Old: day_duration (days)")
        print("  • New: duration_minutes (minutes)")
        print("  • Default: 60 minutes (1 hour)")
        print("\nYou can now use /start_event with minute-based durations!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
