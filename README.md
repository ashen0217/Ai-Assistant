<div align="center">

# 🤖 JARVIS OS — Personal AI Assistant

**A fully local, voice-activated AI desktop assistant with screen awareness, emotional intelligence, and long-term memory.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Electron](https://img.shields.io/badge/Electron-39-47848F?style=for-the-badge&logo=electron&logoColor=white)](https://electronjs.org)
[![Groq](https://img.shields.io/badge/Groq-Llama_4_Scout-F55036?style=for-the-badge)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

*Just say **"Hey Jarvis"** — no cloud, no wake-word subscription, no latency.*

</div>

---

## ✨ Feature Overview

| Capability | Technology | Description |
|---|---|---|
| 🎙️ **Offline Wake Word** | OpenWakeWord + ONNX | Say "Hey Jarvis" — no Picovoice, no API key, completely free |
| 🗣️ **Speech-to-Text** | Groq Whisper Large v3 Turbo | Sub-second cloud transcription of your voice |
| 🧠 **Multimodal Vision AI** | Groq Llama 4 Scout 17B | Reads your screen, understands context, gives precise answers |
| 📢 **Text-to-Speech** | Web Speech API | AI speaks its responses back to you in real time |
| 😊 **Emotion Detection** | DeepFace + OpenCV | Webcam-based facial expression analysis — updates every 5s |
| 💾 **Long-Term Memory** | Pinecone + Gemini Embeddings | Semantic vector memory — Jarvis remembers what helped you before |
| 👤 **User Profile** | MongoDB | Tracks name, tech stack, focus area, emotional state |
| 🖥️ **Desktop UI** | React 19 + Tailwind CSS + Electron | Glassmorphic dark HUD — runs as a native desktop app |
| 🔄 **Live Status Polling** | SSE + REST | Emotion, focus, and profile update in real time every 3s |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    JARVIS OS — System Architecture              │
└─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────┐          ┌──────────────────────────────┐
  │   Electron Desktop  │          │      Python FastAPI Server   │
  │   (React 19 + TW)   │◄─────────│         127.0.0.1:8000       │
  │                     │  REST    │                              │
  │  ┌───────────────┐  │  + SSE   │  ┌────────────────────────┐ │
  │  │ Chat UI / HUD │  │          │  │  /api/chat             │ │
  │  │ Wake Badge    │  │          │  │  /api/transcribe       │ │
  │  │ Emotion Chip  │  │          │  │  /api/status           │ │
  │  │ Mic Button    │  │          │  │  /api/wake-stream (SSE)│ │
  │  └───────────────┘  │          │  └────────────────────────┘ │
  │                     │          │                              │
  │  ┌───────────────┐  │          │  ┌────────────────────────┐ │
  │  │ MediaRecorder │  │          │  │  main_agent.py         │ │
  │  │ (WebM audio)  │──┼──POST───►│  │  ├── Groq Vision API   │ │
  │  └───────────────┘  │          │  │  ├── Screen Capture    │ │
  │                     │          │  │  └── Memory Recall     │ │
  │  ┌───────────────┐  │          │  └────────────────────────┘ │
  │  │ EventSource   │◄─┼──SSE────-│                              │
  │  │ (wake word)   │  │          │  ┌────────────────────────┐ │
  │  └───────────────┘  │          │  │  Wake Word Thread      │ │
  │                     │          │  │  OpenWakeWord (ONNX)   │ │
  │  ┌───────────────┐  │          │  │  sounddevice 16kHz     │ │
  │  │ SpeechSynth   │  │          │  └────────────────────────┘ │
  │  │ (TTS output)  │  │          └──────────────────────────────┘
  │  └───────────────┘  │
  └─────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                     External Services                        │
  │  Groq API         │  Pinecone         │  MongoDB (local)    │
  │  ├── Llama 4 Scout│  (Vector Memory)  │  (User Profile)     │
  │  ├── Whisper v3   │                   │                     │
  │  └── Llama 3.1 8B │  Google Gemini    │  DeepFace           │
  │     (summaries)   │  (Embeddings)     │  (Emotion AI)       │
  └─────────────────────────────────────────────────────────────┘
```

### Complete Voice-to-Voice Pipeline

```
"Hey Jarvis" (spoken)
    │
    ▼
OpenWakeWord (hey_jarvis.onnx) — runs fully offline
    │  score > 0.5
    ▼
SSE push → /api/wake-stream → React EventSource
    │
    ▼
MediaRecorder starts → user speaks question
    │
    ▼
WebM audio blob → POST /api/transcribe
    │
    ▼
Groq Whisper Large v3 Turbo → transcribed text
    │
    ▼
POST /api/chat → main_agent.py
    │  ├── Screen capture (mss + Pillow, 50% downscale)
    │  ├── Long-term memory recall (Pinecone semantic search)
    │  └── User profile (MongoDB emotion + focus + stack)
    ▼
Groq Llama 4 Scout 17B Vision → AI response text
    │  └── Background: Summarize & save fix to Pinecone (daemon thread)
    ▼
React renders message bubble
    │
    ▼
Web Speech API (SpeechSynthesisUtterance) → spoken aloud 🔊
```

---

## 📁 Project Structure

```
Ai-Assistant/
├── server.py               # FastAPI server — all HTTP + SSE endpoints
├── main_agent.py           # Core AI agent — vision, memory, profile
├── emotion_agent.py        # DeepFace webcam emotion tracker (run separately)
├── vector_memory.py        # Pinecone + Gemini vector memory store
├── agent.py                # Standalone CLI agent (optional)
├── db_setup.py             # MongoDB initial profile setup script
├── .env.example            # Template for environment variables
├── .gitignore
├── README.md
│
└── jarvis-dashboard/       # Electron + React 19 frontend
    ├── electron.vite.config.mjs
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── package.json
    └── src/
        ├── main/           # Electron main process
        ├── preload/        # Electron preload scripts
        └── renderer/
            ├── index.html
            └── src/
                ├── main.jsx
                ├── App.jsx     # ← All UI + voice logic lives here
                ├── assets/
                │   └── main.css    # Tailwind v3 + custom animations
                └── components/
                    └── Versions.jsx
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| MongoDB | Community | [mongodb.com](https://www.mongodb.com/try/download/community) |
| Git | Any | [git-scm.com](https://git-scm.com) |

---

### 1. Clone the Repository

```bash
git clone https://github.com/ashen0217/Ai-Assistant.git
cd Ai-Assistant
```

---

### 2. Python Backend Setup

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install all Python dependencies
pip install fastapi uvicorn python-multipart groq openai pymongo \
            pinecone-client google-generativeai google-genai \
            python-dotenv mss Pillow openwakeword sounddevice \
            numpy onnxruntime deepface opencv-python
```

#### Download the offline wake word model

```python
# Run once to download all pre-trained OpenWakeWord models (~50 MB)
python -c "from openwakeword.utils import download_models; download_models()"
```

---

### 3. Environment Variables

Copy the template and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Get free API key at https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Get free API key at https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Get free API key at https://app.pinecone.io
PINECONE_API_KEY=pcsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Local MongoDB (default — no auth required for development)
MONGODB_URI=mongodb://localhost:27017/?directConnection=true
```

> **Never commit your `.env` file.** It is already in `.gitignore`.

---

### 4. Initialize MongoDB Profile

```bash
python db_setup.py
```

This creates your user profile document in the `assistant_memory` database.

---

### 5. Frontend Setup

```bash
cd jarvis-dashboard
npm install
```

---

### 6. Running the Application

You need **two terminal windows** running simultaneously:

#### Terminal 1 — Python Backend
```bash
# From the project root, with venv activated
python server.py
```

Expected output:
```
[SERVER] Jarvis API Server initializing...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
[OWW] Initializing OpenWakeWord engine (hey_jarvis / onnxruntime)...
[OWW] OpenWakeWord ready - listening for 'Hey Jarvis'...
[OWW] Microphone stream open (16 kHz mono)
```

#### Terminal 2 — Electron Desktop App
```bash
cd jarvis-dashboard
npm run dev
```

#### (Optional) Terminal 3 — Emotion Tracker
```bash
# Requires a webcam; updates your emotion in MongoDB every 5 seconds
python emotion_agent.py
```

---

## 🎙️ How to Use

### Voice (Hands-Free)
1. Make sure the backend is running
2. Look for the **👂 Listening** badge in the top-right of the UI — it glows purple when connected
3. Say **"Hey Jarvis"** clearly
4. Speak your question after the status bar shows *"👂 Wake word detected — listening…"*
5. Jarvis transcribes, thinks (with screen context), and speaks the answer back

### Push-to-Talk (Manual)
- **Hold** the 🎤 microphone button → speak → **release** to send
- The button pulses red while recording

### Text Input
- Type in the input box and press **Enter** or click ➤

---

## 🔑 API Keys & Services

| Service | Purpose | Free Tier | Link |
|---|---|---|---|
| **Groq** | LLM inference (Llama 4 + Whisper) | ✅ Generous free tier | [console.groq.com](https://console.groq.com) |
| **Google Gemini** | Text embeddings for vector memory | ✅ Free tier available | [aistudio.google.com](https://aistudio.google.com) |
| **Pinecone** | Vector database (long-term memory) | ✅ Free serverless tier | [app.pinecone.io](https://app.pinecone.io) |
| **MongoDB** | User profile & emotion state | ✅ Local (no account needed) | [mongodb.com](https://www.mongodb.com/try/download/community) |
| **OpenWakeWord** | Offline "Hey Jarvis" wake word | ✅ Completely free + offline | Bundled in pip package |

---

## 🧩 Key Technologies

### Backend
| Package | Role |
|---|---|
| `fastapi` + `uvicorn` | REST API + SSE server |
| `groq` | Whisper STT + Llama 4 Vision + Llama 3.1 summaries |
| `openai` | OpenAI-compatible client for Groq API |
| `openwakeword` + `onnxruntime` | Offline wake word detection |
| `sounddevice` | Low-latency microphone stream at 16 kHz |
| `mss` + `Pillow` | Screen capture + 50% downscale for vision API |
| `pymongo` | MongoDB user profile reads/writes |
| `pinecone-client` | Vector memory upsert + semantic search |
| `google-genai` | Gemini `gemini-embedding-001` (3072-dim vectors) |
| `deepface` + `opencv-python` | Facial emotion analysis from webcam |
| `python-multipart` | Multipart file upload parsing for audio |

### Frontend
| Package | Role |
|---|---|
| `react` 19 + `react-dom` | UI framework |
| `electron` + `electron-vite` | Desktop app wrapper |
| `tailwindcss` v3 | Utility-first CSS with glassmorphic dark theme |
| Web Speech API | `SpeechSynthesisUtterance` — browser-native TTS |
| `MediaRecorder` API | Browser-native WebM audio recording |
| `EventSource` API | SSE client for wake word events |

---

## ⚙️ Configuration Reference

### `server.py` — Key Settings
```python
COOLDOWN_SECONDS = 3.0    # Seconds before wake word can fire again
blocksize = 1280           # ~80ms audio chunks at 16kHz
# Whisper model
model = "whisper-large-v3-turbo"
# Vision model
model = "meta-llama/llama-4-scout-17b-16e-instruct"
```

### `main_agent.py` — Key Settings
```python
timeout = 30.0      # Hard timeout for Groq API calls
max_retries = 2     # Auto-retry on transient errors
quality = 85        # JPEG compression quality for screen captures
scale = 0.5         # Screen downscale factor (reduces token usage)
```

### `vector_memory.py` — Key Settings
```python
EMBED_MODEL = "gemini-embedding-001"    # 3072-dimensional embeddings
top_k = 2                               # Number of past memories to recall
```

---

## 🛠️ Troubleshooting

### "Port 8000 already in use"
```powershell
# Kill the process using port 8000
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
```

### Wake word not triggering
- Check that the **👂 Listening** badge in the UI is purple (SSE connected)
- Say "Hey Jarvis" clearly, 30–60 cm from the mic, in a quiet environment
- Check server terminal for `[OWW] Microphone stream open` message
- Ensure no other app has exclusive mic access

### `tflite-runtime` warning on Windows
This is harmless. The system automatically falls back to `onnxruntime` (already installed). No action needed.

### Groq rate limit (429)
Free tier limits: ~30 RPM for vision models. The app retries automatically. If you hit limits frequently, consider reducing screen capture calls or upgrading your Groq plan.

### MongoDB connection failed
```bash
# Start MongoDB service (Windows)
net start MongoDB

# Or with mongod directly
mongod --dbpath C:\data\db
```

### Pinecone index not found
```bash
python -c "from vector_memory import setup_pinecone; setup_pinecone()"
```

---

## 🗺️ Roadmap

- [ ] **Streaming responses** — stream Llama tokens to UI as they arrive
- [ ] **Multi-monitor support** — select which screen to capture
- [ ] **Custom wake words** — train your own OpenWakeWord model
- [ ] **Plugin system** — add custom tools (web search, code execution, etc.)
- [ ] **Conversation history** — persist full chat sessions to MongoDB
- [ ] **Emotion-adaptive responses** — adjust tone based on detected emotion
- [ ] **Local LLM fallback** — Ollama integration for fully offline mode

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ashen** — [@ashen0217](https://github.com/ashen0217)

---

<div align="center">

Built with ❤️ using Groq, OpenWakeWord, React, and Electron

*"Just say Hey Jarvis."*

</div>
