import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Connect to local MongoDB
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)

# Create or access the databases for your AI
db = client["assistant_memory"]
profile_collection = db["user_profile"]

# Initialize your core profile
profile_collection.update_one(
    {"name": "Ashen"}, 
    {"$set": {
        "current_focus": "Building a personal AI assistant",
        "tech_stack": ["Spring Boot", "React", "Python", "MongoDB"]
    }},
    upsert=True
)

print("Database connected and profile initialized successfully!")