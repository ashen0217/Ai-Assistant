import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pymongo import MongoClient

load_dotenv()

# Initialize Clients
_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not _gemini_key:
    raise EnvironmentError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in the environment.")

client = genai.Client(api_key=_gemini_key)

mongo_client = MongoClient(
    os.getenv("MONGODB_URI"),
    serverSelectionTimeoutMS=5000,
)
db = mongo_client["assistant_memory"]
profile_collection = db["user_profile"]

def fetch_user_profile() -> dict:
    """Retrieves the latest profile data from MongoDB."""
    try:
        profile = profile_collection.find_one({"name": "Ashen"})
        if not profile:
            return {"current_focus": "Unknown", "tech_stack": []}
        return profile
    except Exception as e:
        print(f"[Warning] MongoDB fetch failed: {e}. Using default profile.")
        return {"current_focus": "Unknown", "tech_stack": []}

def get_ai_response(user_input: str) -> str:
    """Calls Gemini with exponential backoff on transient errors."""
    profile = fetch_user_profile()
    current_focus = profile.get("current_focus", "N/A")
    tech_stack = ", ".join(profile.get("tech_stack", []))

    system_instruction = (
        "You are an elite, proactive personal AI assistant for Ashen.\n"
        f"His current focus is: {current_focus}.\n"
        f"His core tech stack includes: {tech_stack}.\n\n"
        "Your job is to look at his inputs and provide highly contextual, "
        "concise engineering guidance."
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",   # Updated from decommissioned gemini-3.1-flash-lite
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "503" in err or "429" in err or "overloaded" in err.lower():
                wait = 2 ** attempt   # Exponential backoff: 1s, 2s, 4s
                print(f"[Retry {attempt + 1}/{max_retries}] API busy — waiting {wait}s...")
                time.sleep(wait)
            else:
                return f"Error: {err}"

    return "The AI servers are currently overloaded. Please try again in a moment."

if __name__ == "__main__":
    print("🧠 AI Brain connected to MongoDB. Ready for instructions:\n")
    while True:
        try:
            user_msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Shutting down gracefully...")
            break

        if user_msg.lower() == "exit":
            break

        if not user_msg:
            continue

        print("\nThinking...")
        ai_msg = get_ai_response(user_msg)
        print(f"\nAssistant: {ai_msg}\n" + "-" * 50)