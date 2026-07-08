import os
from pymongo import MongoClient

# Get MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Strip quotes if present
if MONGODB_URI and MONGODB_URI.startswith('"') and MONGODB_URI.endswith('"'):
    MONGODB_URI = MONGODB_URI[1:-1]
elif MONGODB_URI and MONGODB_URI.startswith("'") and MONGODB_URI.endswith("'"):
    MONGODB_URI = MONGODB_URI[1:-1]

if not MONGODB_URI:
    MONGODB_URI = "mongodb://localhost:27017/autodev"

# We will initialize the client locally when imported
client = MongoClient(MONGODB_URI)

# Use a specific database if no default in URI
if MONGODB_URI and ("?" in MONGODB_URI or "/" not in MONGODB_URI.split("://")[1]):
    try:
        db = client.get_database()
    except Exception:
        db = client["autodev"]
else:
    db = client.get_database()

def get_db():
    try:
        yield db
    finally:
        pass
