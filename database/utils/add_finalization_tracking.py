#!/usr/bin/env python3
"""
Migration script to add is_finalized column to events table.
This fixes the race condition where ended events can't be found for auto-finalization.
"""

import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Add is_finalized column to events table"""
    
    print("=" * 60)
    print("MIGRATION: Add is_finalized tracking to events")
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
        
        # Check if is_finalized column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'events' AND column_name = 'is_finalized'
        """)
        
        if cursor.fetchone():
            print("✅ Migration already complete! is_finalized column exists.")
            print("\nChecking current schema...")
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'events' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("\nCurrent events table columns:")
            for col in columns:
                print(f"  • {col[0]} ({col[1]}) default: {col[2]}")
            return
        
        print("\n📋 Steps:")
        print("1. Add is_finalized INTEGER column (0 = not finalized, 1 = finalized)")
        print("2. Set existing events to finalized = 1")
        print("3. Create index for faster queries")
        print("4. Add constraint to ensure only 0 or 1 values")
        
        input("\nPress Enter to continue or Ctrl+C to cancel...")
        
        # Step 1: Add new column
        print("\n➡️  Adding is_finalized column...")
        cursor.execute("ALTER TABLE events ADD COLUMN is_finalized INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Column added")
        
        # Step 2: Set existing events as finalized
        print("\n➡️  Marking existing events as finalized...")
        cursor.execute("UPDATE events SET is_finalized = 1")
        rows_updated = cursor.rowcount
        conn.commit()
        print(f"✅ Updated {rows_updated} existing events")
        
        # Step 3: Create index
        print("\n➡️  Creating index...")
        cursor.execute("CREATE INDEX idx_events_is_finalized ON events(is_finalized)")
        conn.commit()
        print("✅ Index created")
        
        # Step 4: Add constraint
        print("\n➡️  Adding constraint...")
        cursor.execute("ALTER TABLE events ADD CONSTRAINT check_is_finalized CHECK (is_finalized IN (0, 1))")
        conn.commit()
        print("✅ Constraint added")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  • Added is_finalized INTEGER column to events table")
        print(f"  • Marked {rows_updated} existing events as finalized (1)")
        print("  • Created index for performance")
        print("  • Added constraint: is_finalized IN (0, 1)")
        print("\n  Values: 0 = not finalized, 1 = finalized")
        print("\nThis fixes the auto-finalization race condition!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
