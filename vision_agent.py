import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize the Gemini Client with explicit API key
_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not _gemini_key:
    raise EnvironmentError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in the environment.")

client = genai.Client(api_key=_gemini_key)

SYSTEM_INSTRUCTION = """
You are Ashen's personal AI assistant. Look closely at the provided screenshot of his laptop.
Describe exactly what he is working on.
If you see code, mention the language and what it does.
If you see an error, point it out immediately.
Keep it strictly under 3 sentences.
"""

def capture_screen_bytes() -> bytes:
    """Captures the primary monitor and returns raw PNG bytes in memory."""
    import mss
    import mss.tools
    with mss.MSS() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        return mss.tools.to_png(sct_img.rgb, sct_img.size)

def analyze_screen():
    """Sends the screen bytes to Gemini to see what you are working on."""
    print("📸 Snapping screen...")
    try:
        image_bytes = capture_screen_bytes()
    except Exception as e:
        print(f"[Screen capture error]: {e}")
        return

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",   # Updated from decommissioned gemini-3.1-flash-lite
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                "Analyze my screen. What am I doing right now?",
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,   # Low temperature so it doesn't hallucinate code
            ),
        )
        print(f"\n🧠 AI Observation:\n{response.text}\n")
    except Exception as e:
        print(f"[Vision Error]: {str(e)}")

if __name__ == "__main__":
    print("👁️ Vision sensor activated. Press Ctrl+C to stop.")
    try:
        while True:
            analyze_screen()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nVision sensor deactivated.")