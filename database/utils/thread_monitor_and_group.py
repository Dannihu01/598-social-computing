import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


SQL_PATH = os.path.join(
    Path(__file__).resolve().parents[1], "DDL", "add_thread_monitoring.sql")

if __name__ == "__main__":
    # connection establishment
    conn = psycopg2.connect(
        host=os.environ.get("DATABASE_HOST"),
        user=os.environ.get("DATABASE_USER"),
        password=os.environ.get("DATABASE_PASSWORD"),
        port=os.environ.get("DATABASE_PORT"),
        connect_timeout=10
    )
    conn.autocommit = True

    with open(SQL_PATH, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    # Creating a cursor object
    cursor = conn.cursor()
    cursor.execute(sql_script)

    # Closing the connection
    conn.close()
