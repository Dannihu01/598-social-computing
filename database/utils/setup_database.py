#!/usr/bin/env python3
"""
Database setup script.
This script helps you set up the database connection and create the schema.
"""

import sys
import os
from dotenv import load_dotenv

# Add the project root directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

from database.db import init_pool, close_pool
from database.utils.create_schema import create_schema

def setup_database():
    print("Setting up database...")
    print("=" * 50)
    dsn = f"dbname={os.environ.get('DATABASE_NAME')} user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']} host={os.environ['DATABASE_HOST']} port={os.environ.get('DATABASE_PORT',5432)}"
    
    try:
        # Initialize database pool
        init_pool(dsn)
        print("✓ Database connection established!")
        
        # Create schema
        print("Creating database schema...")
        create_schema()
        print("✓ Database schema created successfully!")
        
        print("\n" + "=" * 50)
        print("Database setup completed successfully!")
        print("\nYou can now run:")
        print("python test_events_with_db.py")
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Create a database: createdb social_computing")
        print("3. Set environment variables in .env file:")
        print("   DB_HOST=localhost")
        print("   DB_PORT=5432")
        print("   DB_NAME=social_computing")
        print("   DB_USER=your_username")
        print("   DB_PASSWORD=your_password")
        
    finally:
        close_pool()

if __name__ == "__main__":
    setup_database()
