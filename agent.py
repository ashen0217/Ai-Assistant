import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient

load_dotenv()

# ─── Ollama Client (OpenAI-compatible local endpoint) ────────────────────────
ollama_client = OpenAI(
    api_key="ollama",                      # Ollama doesn't require a real key
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

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
    """Calls local Ollama model with exponential backoff on transient errors."""
    profile = fetch_user_profile()
    current_focus = profile.get("current_focus", "N/A")
    tech_stack = ", ".join(profile.get("tech_stack", []))

    system_instruction = (
        "You are Jarvis, an elite proactive personal AI assistant for Ashen.\n"
        f"His current focus is: {current_focus}.\n"
        f"His core tech stack includes: {tech_stack}.\n\n"
        "Your job is to look at his inputs and provide highly contextual, "
        "concise engineering guidance."
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = ollama_client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            wait = 2 ** attempt   # Exponential backoff: 1s, 2s, 4s
            print(f"[Retry {attempt + 1}/{max_retries}] Ollama error — waiting {wait}s... ({err})")
            time.sleep(wait)

    return "Ollama is currently unavailable. Make sure `ollama serve` is running."

if __name__ == "__main__":
    print(f"🧠 AI Brain connected to MongoDB. Running on Ollama ({OLLAMA_MODEL}). Ready:\n")
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