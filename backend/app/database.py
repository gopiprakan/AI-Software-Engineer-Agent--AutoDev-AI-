import os
from pymongo import MongoClient

# Get MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# We will initialize the client locally when imported
client = MongoClient(MONGODB_URI)
db = client.get_database() # Uses the database specified in the URI, or 'test' by default

def get_db():
    try:
        yield db
    finally:
        pass

