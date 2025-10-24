import sys
import os
from dotenv import load_dotenv

# Add the project root directory to the path so we can import our modules
# This script is in database/examples/, so we need to go up 2 levels to reach project root
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import database modules after path setup - using dynamic imports to avoid IDE reordering


def import_database_modules():
    global create_event, get_active_event, init_pool, close_pool, add_response, get_user_by_slack_id, delete_all_events
    from database.repos.events import create_event, get_active_event, delete_all_events
    from database.repos.users import get_user_by_slack_id
    from database.db import init_pool, close_pool
    from database.repos.responses import add_response


load_dotenv()


def main():
    # Import database modules
    import_database_modules()

    print("Users adding responses example...")
    print("=" * 50)

    # Initialize database connection
    # You'll need to replace this with your actual database connection string
    dsn = f"dbname={os.environ.get('DATABASE_NAME')} user={os.environ['DATABASE_USER']} password={os.environ['DATABASE_PASSWORD']} host={os.environ['DATABASE_HOST']} port={os.environ.get('DATABASE_PORT',5432)}"

    try:
        print("Initializing database connection...")
        init_pool(dsn)
        print("Database connection initialized!")

        user = get_user_by_slack_id(slack_id="therkels")
        print(user)
        if not get_active_event():
            create_event()
            print("Event created!")
        else:
            print("Event already created!")
        print("Adding responses...")
        print("=" * 50)

        print("Adding response for user 1...")
        result = add_response(user_slack_id="therkels",
                              response="I think the event is okay!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        delete_all_events()
        close_pool()
        print("Database connection closed!")


if __name__ == "__main__":
    main()
