import os
import threading
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient

# Import your vector memory functions (Ollama handles embeddings locally)
from vector_memory import recall, remember_this

load_dotenv()

# ─── Ollama Client (OpenAI-compatible local endpoint) ────────────────────────
# Make sure Ollama is running: `ollama serve`
# Make sure the model is pulled: `ollama pull qwen2.5:3b`
#
# NOTE: .env stores OLLAMA_BASE_URL without /v1 (e.g. http://localhost:11434)
# so that vector_memory.py can use it for raw /api/embeddings calls.
# The OpenAI-compatible client requires the /v1 suffix, so we add it here
# defensively (stripping any accidental trailing /v1 first to avoid doubling).
_ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
if _ollama_base.endswith("/v1"):
    _ollama_v1_url = _ollama_base
else:
    _ollama_v1_url = f"{_ollama_base}/v1"

ollama_client = OpenAI(
    api_key="ollama",          # Ollama doesn't require a real key
    base_url=_ollama_v1_url,   # Must be http://host:port/v1
)


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Initialize MongoDB with a sensible server selection timeout
mongo_client = MongoClient(
    os.getenv("MONGODB_URI"),
    serverSelectionTimeoutMS=5000,   # Fail fast if MongoDB is unreachable
)
db = mongo_client["assistant_memory"]
profile_collection = db["user_profile"]

def fetch_user_profile() -> dict:
    """Retrieves the latest profile data from MongoDB with a fallback."""
    try:
        profile = profile_collection.find_one({"name": "Ashen"})
        if not profile:
            return {"current_focus": "Building an AI", "tech_stack": ["Python"], "current_emotion": "neutral"}
        return profile
    except Exception as e:
        print(f"[Warning] MongoDB fetch failed: {e}. Using default profile.")
        return {"current_focus": "Building an AI", "tech_stack": ["Python"], "current_emotion": "neutral"}

def summarize_and_save(user_msg: str, ai_response: str):
    """Background task using Ollama to summarize and Pinecone to save."""
    try:
        summary_prompt = (
            "Analyze this interaction. If it contains a specific technical problem and a solution, "
            "summarize the fix in exactly 1 or 2 clear sentences.\n"
            "If it is just a greeting, casual chat, or does NOT contain a concrete code fix, "
            "reply with EXACTLY the word: SKIP\n\n"
            f"User: {user_msg}\nAI: {ai_response}"
        )
        response = ollama_client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()

        # Apply the Junk Filter
        if summary.upper() != "SKIP":
            remember_this(summary, category="auto-learned-fix")
        else:
            print("[Memory ignored: No technical fix to save]")

    except Exception as e:
        print(f"[Background save error]: {e}")

def get_vision_response(user_input: str) -> str:
    """
    Sends user input to the local Ollama qwen2.5:3b model with full context.
    Note: Screen capture/vision is not supported by qwen2.5:3b — text-only mode.
    """
    profile = fetch_user_profile()
    current_focus = profile.get("current_focus", "N/A")
    tech_stack = ", ".join(profile.get("tech_stack", []))
    current_emotion = profile.get("current_emotion", "neutral")

    print("\n[Searching long-term memory...]")
    past_knowledge = recall(user_input)

    system_message = (
        "You are Jarvis, an advanced personal AI assistant running fully locally.\n"
        f"The engineer you are helping is named Ashen.\n"
        f"His Focus: '{current_focus}', Stack: [{tech_stack}].\n"
        f"He is currently feeling: {current_emotion}.\n"
        f"Past knowledge of fixes:\n{past_knowledge}\n\n"
        "Provide a precise, concise engineering solution. "
        "Address him by name occasionally."
    )

    print(f"[Ollama] Sending request to {OLLAMA_MODEL} at {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')}...")

    try:
        response = ollama_client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
        )

        ai_text = response.choices[0].message.content

        # Save memory in background using a daemon thread so it doesn't block exit
        t = threading.Thread(target=summarize_and_save, args=(user_input, ai_text), daemon=True)
        t.start()

        return ai_text

    except Exception as e:
        return f"Ollama Error: {str(e)}\n\nMake sure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull {OLLAMA_MODEL}`)."

if __name__ == "__main__":
    print(f"🤖 Jarvis Agent Online — Powered by {OLLAMA_MODEL} via Ollama (MongoDB + Pinecone Active).")
    print("Type 'exit' to quit.\n")

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

        ai_msg = get_vision_response(user_msg)
        print(f"\nAssistant:\n{ai_msg}\n")
        print("-" * 60)