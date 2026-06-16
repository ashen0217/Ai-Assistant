import os
import sys

# ─── Load .env FIRST — before any import that reads environment variables ─────
# In dev mode: load_dotenv() finds .env in CWD (repo root where server.py lives)
# Packaged mode (core_engine.exe): sys.executable is the exe path; .env sits
# alongside it in the same backend-dist/ directory, so we point dotenv there.
from dotenv import load_dotenv
if getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    _env_path = os.path.join(_exe_dir, '.env')
    print(f"[SERVER] Packaged mode — loading .env from: {_env_path}")
    load_dotenv(dotenv_path=_env_path, override=True)
else:
    load_dotenv()   # Dev mode: finds .env in CWD (repo root)

import shutil
import queue
import threading
import time
import numpy as np
import sounddevice as sd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from main_agent import get_vision_response, fetch_user_profile


# ─── Optional: OpenWakeWord (requires onnxruntime — may fail in packaged exe) ──────
try:
    from openwakeword.model import Model as OWWModel
    OWW_AVAILABLE = True
    print("[OWW] openwakeword loaded successfully.")
except Exception as _oww_err:
    OWWModel = None
    OWW_AVAILABLE = False
    print(f"[OWW] WARNING: openwakeword unavailable — wake word detection disabled.")
    print(f"[OWW] Reason: {_oww_err}")
    print("[OWW] All other Jarvis features (chat, STT, vision) remain fully functional.")


# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Jarvis Backend API")

# CORS must be added BEFORE any route is evaluated
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client — ONLY used for Whisper audio transcription (Ollama doesn't support STT)
# If you don't need voice input, GROQ_API_KEY is not required.
_groq_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=_groq_key) if _groq_key else None

# ─── Shared wake-word event queue (one slot per detection) ────────────────────
wake_queue: queue.Queue = queue.Queue()

# ─── Offline Wake Word Engine (runs in daemon thread) ────────────────────────
def wake_word_thread():
    """
    Continuously listens on the system microphone using OpenWakeWord with the
    hey_jarvis ONNX model. When the wake word is detected it puts a WAKE event
    into wake_queue so the SSE endpoint can forward it to the React UI.
    """
    if not OWW_AVAILABLE:
        print("[OWW] Wake word engine skipped (openwakeword unavailable in packaged mode).")
        return

    print("[OWW] Initializing OpenWakeWord engine (hey_jarvis / onnxruntime)...")
    try:
        oww = OWWModel(
            wakeword_models=["hey_jarvis"],
            inference_framework="onnx",    # works on Windows without tflite-runtime
        )
        print("[OWW] OpenWakeWord ready - listening for 'Hey Jarvis'...")

        # Cooldown: ignore further detections for N seconds after one fires
        COOLDOWN_SECONDS = 3.0
        last_detected_at  = 0.0

        def audio_callback(indata, frames, time_info, status):
            nonlocal last_detected_at
            # Convert float32 mic data → int16 expected by OpenWakeWord
            audio_chunk = (indata[:, 0] * 32767).astype(np.int16)

            prediction = oww.predict(audio_chunk)

            for model_name, score in prediction.items():
                now = time.time()
                if score > 0.5 and (now - last_detected_at) > COOLDOWN_SECONDS:
                    print(f"\n[OWW] Wake word '{model_name}' detected! (score={score:.3f})")
                    last_detected_at = now
                    wake_queue.put("WAKE")

        # Open the mic stream at 16 kHz mono (required by OpenWakeWord)
        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="float32",
            blocksize=1280,          # ~80 ms chunks
            callback=audio_callback,
        ):
            print("[OWW] Microphone stream open (16 kHz mono)")
            while True:
                sd.sleep(1000)       # keep the thread alive

    except Exception as exc:
        print(f"[OWW] ERROR - Wake word engine failed: {exc}")
        print("[OWW] The rest of the server is still running normally.")

# Boot the wake word engine when the module loads
threading.Thread(target=wake_word_thread, daemon=True, name="wake-word").start()

# ─── SSE: push wake events to React ──────────────────────────────────────────
@app.get("/api/wake-stream")
async def wake_stream():
    """
    Server-Sent Events endpoint.  React connects once and waits.
    Every time Python detects 'Hey Jarvis', it fires 'data: WAKE_DETECTED'.
    """
    def event_generator():
        # Send a heartbeat comment every 15 s so the connection stays alive
        # through proxies and Electron's internal HTTP layer.
        last_heartbeat = time.time()
        while True:
            try:
                # Non-blocking check — 1 s timeout so heartbeat can fire
                msg = wake_queue.get(timeout=1.0)
                if msg == "WAKE":
                    yield "data: WAKE_DETECTED\n\n"
            except queue.Empty:
                # Heartbeat: SSE comment lines keep the connection alive
                if time.time() - last_heartbeat >= 15:
                    yield ": heartbeat\n\n"
                    last_heartbeat = time.time()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if present
        },
    )

# ─── Existing endpoints ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

@app.get("/api/status")
def get_status():
    """Returns live profile data, including your current emotion from MongoDB."""
    try:
        profile = fetch_user_profile()
        return {
            "name"           : profile.get("name", "Ashen"),
            "current_focus"  : profile.get("current_focus", "N/A"),
            "current_emotion": profile.get("current_emotion", "neutral"),
            "tech_stack"     : profile.get("tech_stack", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_endpoint(payload: ChatRequest):
    """Sends message to local Ollama qwen2.5:3b model with memory context."""
    try:
        print(f"[CHAT] Received UI message: {payload.message}")
        ai_response = get_vision_response(payload.message)
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file (webm/wav/mp3), sends it to Groq Whisper,
    and returns the transcription as JSON: {"text": "..."}.
    Requires GROQ_API_KEY to be set. Returns 503 if unavailable.
    """
    if groq_client is None:
        raise HTTPException(
            status_code=503,
            detail="Voice transcription is unavailable: GROQ_API_KEY is not configured.",
        )

    temp_path = "temp_audio.webm"
    try:
        with open(temp_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        print(f"[STT] Transcribing: {file.filename} ({file.content_type})")

        with open(temp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=(file.filename or "audio.webm", audio_file),
                response_format="text",
            )

        text = transcription if isinstance(transcription, str) else transcription.text
        print(f"[STT] Transcription result: {text}")
        return {"text": text}

    except Exception as e:
        print(f"[STT] ERROR - Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    print(f"[SERVER] Jarvis API Server initializing...")
    print(f"[SERVER] AI Model: {ollama_model} @ {ollama_url}")
    print(f"[SERVER] Voice STT: {'Groq Whisper (active)' if os.getenv('GROQ_API_KEY') else 'Disabled (no GROQ_API_KEY)'}")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)