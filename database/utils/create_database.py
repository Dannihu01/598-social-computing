import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

# connection establishment
conn = psycopg2.connect(
    host=os.environ.get("DATABASE_HOST"),
    user=os.environ.get("DATABASE_USER"),
    password=os.environ.get("DATABASE_PASSWORD"),
    port=os.environ.get("DATABASE_PORT"),
    connect_timeout=10
)
conn.autocommit = True

# Creating a cursor object
cursor = conn.cursor()

# query to create a database 
sql = '''CREATE database slackbot_dev'''

# executing above query
cursor.execute(sql)
print("Database has been created successfully !!")

# Closing the connection
conn.close()