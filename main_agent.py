import os
import time
import threading
import base64
import mss
import mss.tools
from PIL import Image
import io
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient

# Import your vector memory functions (Gemini still handles embeddings in the background)
from vector_memory import recall, remember_this

load_dotenv()

# 1. Initialize the Groq Client (using the OpenAI library)
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    timeout=30.0,       # Hard timeout: 30s for any API call
    max_retries=2,      # Auto-retry on transient network errors
)

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

def capture_screen_base64() -> str:
    """Captures the screen, downscales it, and converts it to a lightweight JPEG Base64 string."""
    with mss.MSS() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)

        # Downscale by 50% to ensure fast API responses and stay under Groq's 4MB limit
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        new_size = (int(img.width * 0.5), int(img.height * 0.5))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to Base64 using JPEG compression
        byte_io = io.BytesIO()
        img.save(byte_io, format='JPEG', quality=85)
        return base64.b64encode(byte_io.getvalue()).decode('utf-8')

def summarize_and_save(user_msg: str, ai_response: str):
    """Background task using Groq to summarize and Pinecone to save."""
    try:
        summary_prompt = (
            "Analyze this interaction. If it contains a specific technical problem and a solution, "
            "summarize the fix in exactly 1 or 2 clear sentences.\n"
            "If it is just a greeting, casual chat, or does NOT contain a concrete code fix, "
            "reply with EXACTLY the word: SKIP\n\n"
            f"User: {user_msg}\nAI: {ai_response}"
        )
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",   # The fast text model for background summaries
            messages=[{"role": "user", "content": summary_prompt}],
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
    """Combines context and sends it to Groq's Llama 4 Scout Vision model."""

    profile = fetch_user_profile()
    current_focus = profile.get("current_focus", "N/A")
    tech_stack = ", ".join(profile.get("tech_stack", []))
    current_emotion = profile.get("current_emotion", "neutral")

    print("\n[Searching long-term memory...]")
    past_knowledge = recall(user_input)

    system_message = (
        "You are an advanced multimodal personal AI assistant.\n"
        f"The human engineer you are helping is named Ashen.\n"
        f"His Focus: '{current_focus}', Stack: [{tech_stack}].\n"
        f"He is currently feeling: {current_emotion}.\n"
        f"Past knowledge of fixes:\n{past_knowledge}\n\n"
        "Analyze his screen and his message. Provide a precise, concise engineering solution. "
        "Address him by name occasionally."
    )

    print("[Capturing screen & processing via Groq Vision...]")
    base64_image = capture_screen_base64()
    image_url = f"data:image/jpeg;base64,{base64_image}"

    try:
        # Llama 4 Scout is the current recommended Groq vision model (replaces deprecated llama-3.2-11b-vision-preview)
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_input},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )

        ai_text = response.choices[0].message.content

        # Save memory in background using a daemon thread so it doesn't block exit
        t = threading.Thread(target=summarize_and_save, args=(user_input, ai_text), daemon=True)
        t.start()

        return ai_text

    except Exception as e:
        return f"Groq Vision Error: {str(e)}"

if __name__ == "__main__":
    print("🤖 Groq Vision Agent Online (MongoDB + Pinecone + Screen Eyes Active).")
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