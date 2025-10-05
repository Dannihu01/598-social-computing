import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class ClientConfig():
    def __init__(self, host: str, user:str, password: str, port:int = 5432, connect_timeout: int = 10) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.connection_timeout = connect_timeout

conn = psycopg2.connect(
    host=os.environ.get("DATABASE_HOST"),
    user=os.environ.get("DATABASE_USER"),
    password=os.environ.get("DATABASE_PASSWORD"),
    port=os.environ.get("DATABASE_PORT"),
    connect_timeout=10,
    database=os.environ.get("DATABASE_NAME")
)

try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        print(cursor.fetchone())
finally:
    conn.close()