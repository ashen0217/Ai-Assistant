import { useState, useEffect, useRef, useCallback } from 'react'

// ─── Constants ────────────────────────────────────────────────────────────────
const API_BASE = 'http://127.0.0.1:8000'

// ─── Text-to-Speech utility ───────────────────────────────────────────────────
function speak(text) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = 1.05
  utterance.pitch = 0.9
  utterance.volume = 1
  const voices = window.speechSynthesis.getVoices()
  const preferred = voices.find(
    (v) => v.name.includes('Google UK English Male') || v.name.includes('Microsoft David')
  )
  if (preferred) utterance.voice = preferred
  window.speechSynthesis.speak(utterance)
}

// ─── Emotion config ───────────────────────────────────────────────────────────
const emotionEmoji = {
  happy: '😊', sad: '😔', focused: '🎯',
  neutral: '😐', excited: '🚀', stressed: '😰', angry: '😠'
}

// ─── Feature Matrix Data ──────────────────────────────────────────────────────
const FEATURES = [
  {
    icon: '🎙️',
    title: 'Wake Word Activation',
    badge: 'OFFLINE',
    badgeColor: 'text-emerald-400 bg-emerald-400/10 border-emerald-500/30',
    description:
      'Offline "Hey Jarvis" detection via OpenWakeWord (ONNX runtime). Zero cloud dependency — runs entirely on-device at 16 kHz mono.',
    tech: ['OpenWakeWord', 'ONNX Runtime', 'SoundDevice'],
  },
  {
    icon: '👁️',
    title: 'Multimodal Vision',
    badge: 'API',
    badgeColor: 'text-violet-400 bg-violet-400/10 border-violet-500/30',
    description:
      'Screenshots your desktop and sends the image to Gemini 2.5 Flash for real-time code analysis and error detection. Requires GEMINI_API_KEY.',
    tech: ['Google Gemini', 'MSS Screen Capture', 'vision_agent.py'],
  },
  {
    icon: '🧠',
    title: 'Long-Term Memory',
    badge: 'SEMANTIC',
    badgeColor: 'text-cyan-400 bg-cyan-400/10 border-cyan-500/30',
    description:
      'Stores and recalls past fixes using semantic vector search. Embeddings are generated locally via nomic-embed-text (Ollama) and stored in Pinecone.',
    tech: ['Pinecone Serverless', 'nomic-embed-text', 'Ollama'],
  },
  {
    icon: '💬',
    title: 'Local AI Chat',
    badge: 'LOCAL',
    badgeColor: 'text-amber-400 bg-amber-400/10 border-amber-500/30',
    description:
      'Fully offline conversational AI powered by Ollama qwen2.5:3b. No API keys required for chat. Adapts tone based on your current emotion from MongoDB.',
    tech: ['Ollama', 'qwen2.5:3b', 'FastAPI /api/chat'],
  },
  {
    icon: '🔊',
    title: 'Voice Transcription (STT)',
    badge: 'API',
    badgeColor: 'text-violet-400 bg-violet-400/10 border-violet-500/30',
    description:
      'Transcribes microphone input via Groq Whisper large-v3-turbo. Hold the 🎤 button or trigger via wake word. Requires GROQ_API_KEY.',
    tech: ['Groq Whisper', 'whisper-large-v3-turbo', 'MediaRecorder API'],
  },
  {
    icon: '🗣️',
    title: 'Text-to-Speech (TTS)',
    badge: 'BUILT-IN',
    badgeColor: 'text-slate-400 bg-slate-400/10 border-slate-500/30',
    description:
      'Speaks AI responses aloud using the browser-native Web Speech API. Prefers Google UK English Male or Microsoft David voice for a Jarvis-like tone.',
    tech: ['Web Speech API', 'SpeechSynthesisUtterance', 'Browser Native'],
  },
  {
    icon: '😊',
    title: 'Emotion Awareness',
    badge: 'ADAPTIVE',
    badgeColor: 'text-pink-400 bg-pink-400/10 border-pink-500/30',
    description:
      'Reads your current mood from MongoDB and injects it into the AI system prompt, allowing Jarvis to adapt its communication style in real time.',
    tech: ['MongoDB', 'emotion_agent.py', 'User Profile Collection'],
  },
  {
    icon: '⚡',
    title: 'FastAPI REST Backend',
    badge: 'CORE',
    badgeColor: 'text-indigo-400 bg-indigo-400/10 border-indigo-500/30',
    description:
      'Python FastAPI server running at 127.0.0.1:8000. Exposes four endpoints: chat, status, audio transcription, and SSE wake-word stream.',
    tech: ['/api/chat', '/api/status', '/api/transcribe', '/api/wake-stream'],
  },
]

// ─── Feature Matrix Overlay ───────────────────────────────────────────────────
function FeatureMatrix({ onClose }) {
  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    /* Full-screen backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(2, 6, 23, 0.85)', backdropFilter: 'blur(8px)' }}
      onClick={onClose}
    >
      {/* Panel — stop propagation so clicking inside doesn't close */}
      <div
        className="feature-matrix-panel relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border border-indigo-500/25 shadow-[0_0_80px_rgba(99,102,241,0.15)]"
        style={{
          background: 'linear-gradient(135deg, rgba(15,23,42,0.97) 0%, rgba(23,12,60,0.97) 100%)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative glow blobs */}
        <div className="pointer-events-none absolute -top-32 -left-32 w-64 h-64 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.6) 0%, transparent 70%)' }} />
        <div className="pointer-events-none absolute -bottom-32 -right-32 w-64 h-64 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.6) 0%, transparent 70%)' }} />

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-indigo-500/20">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-sm font-bold shadow-[0_0_16px_rgba(124,58,237,0.5)]">
                ⬡
              </div>
              <h2 className="text-lg font-bold tracking-[2px] text-white">JARVIS CAPABILITIES</h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-mono">
                v1.0 · {FEATURES.length} modules
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500 pl-11">Three-Tier AI Architecture — Python FastAPI · React · Electron</p>
          </div>
          <button
            id="feature-matrix-close"
            onClick={onClose}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800/80 transition-all text-lg"
            title="Close (Esc)"
          >
            ×
          </button>
        </div>

        {/* Scrollable grid */}
        <div className="overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 90px)' }}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FEATURES.map((feat, i) => (
              <FeatureCard key={i} feat={feat} index={i} />
            ))}
          </div>

          {/* Footer note */}
          <div className="mt-6 pt-4 border-t border-slate-800 text-center">
            <p className="text-[11px] text-slate-600 tracking-wide">
              Press <kbd className="bg-slate-800 border border-slate-700 rounded px-1 text-slate-400">Esc</kbd> or click outside to close
              &nbsp;·&nbsp;
              API docs at{' '}
              <a
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 hover:text-indigo-300 transition-colors underline underline-offset-2"
              >
                127.0.0.1:8000/docs
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ feat, index }) {
  return (
    <div
      className="feature-card group relative rounded-xl border border-slate-700/60 p-4 overflow-hidden transition-all duration-300 hover:border-indigo-500/50 hover:shadow-[0_0_24px_rgba(99,102,241,0.12)]"
      style={{
        background: 'rgba(15, 23, 42, 0.7)',
        animationDelay: `${index * 60}ms`,
      }}
    >
      {/* Hover shimmer */}
      <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl"
        style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.05) 0%, transparent 60%)' }} />

      {/* Card header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl leading-none">{feat.icon}</span>
          <h3 className="text-sm font-semibold text-white leading-tight">{feat.title}</h3>
        </div>
        <span className={`shrink-0 text-[10px] font-bold tracking-widest px-2 py-0.5 rounded-full border ${feat.badgeColor}`}>
          {feat.badge}
        </span>
      </div>

      {/* Description */}
      <p className="text-xs text-slate-400 leading-relaxed mb-3">{feat.description}</p>

      {/* Tech tags */}
      <div className="flex flex-wrap gap-1.5">
        {feat.tech.map((t) => (
          <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/50 text-slate-500 font-mono">
            {t}
          </span>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
function App() {
  const [status, setStatus] = useState({
    name: 'Loading…',
    current_emotion: 'neutral',
    current_focus: '…',
    tech_stack: []
  })
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: "Hello! I'm Jarvis — your AI assistant. Say \"Hey Jarvis\" or hold 🎤 to speak."
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [wakeWordActive, setWakeWordActive] = useState(false)
  const [showFeatureMatrix, setShowFeatureMatrix] = useState(false)

  const mediaRecorderRef = useRef(null)
  const audioChunksRef  = useRef([])
  const chatEndRef       = useRef(null)
  // ← Ref that always points at the LATEST startRecording — prevents stale closure
  // in the SSE useEffect which runs once with [] deps.
  const startRecordingRef = useRef(null)

  // ── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── Poll live profile & emotion every 3s ────────────────────────────────
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res  = await fetch(`${API_BASE}/api/status`)
        const data = await res.json()
        setStatus(data)
      } catch {
        /* server might not be up yet */
      }
    }
    fetchStatus()
    const interval = setInterval(fetchStatus, 3000)
    return () => clearInterval(interval)
  }, [])

  // ── Send message to AI ───────────────────────────────────────────────────
  const sendMessage = useCallback(async (overrideText) => {
    const userText = (overrideText ?? input).trim()
    if (!userText || loading) return

    const newMsgs = [...messages, { role: 'user', text: userText }]
    setMessages(newMsgs)
    setInput('')
    setLoading(true)
    setStatusMsg('Thinking…')

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ message: userText })
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data   = await res.json()
      const aiText = data.response || 'No response received.'
      setMessages([...newMsgs, { role: 'ai', text: aiText }])
      setStatusMsg('')
      speak(aiText)                        // 🔊 Speak the AI reply aloud
    } catch (err) {
      setMessages([...newMsgs, { role: 'ai', text: `Error: ${err.message}` }])
      setStatusMsg('')
    } finally {
      setLoading(false)
    }
  }, [input, loading, messages])

  // ── Start voice recording ────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    if (isRecording || loading) return
    // Stop any ongoing TTS so mic picks up user speech cleanly
    window.speechSynthesis?.cancel()

    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunksRef.current = []

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())

        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        if (blob.size < 1000) {
          setStatusMsg('Recording too short — try again.')
          setTimeout(() => setStatusMsg(''), 2500)
          return
        }

        setStatusMsg('Transcribing…')
        try {
          const formData = new FormData()
          formData.append('file', blob, 'recording.webm')

          const res = await fetch(`${API_BASE}/api/transcribe`, {
            method: 'POST',
            body  : formData
          })
          if (!res.ok) throw new Error(`Transcription error ${res.status}`)
          const data       = await res.json()
          const transcript = data.text?.trim()

          if (transcript) {
            setStatusMsg('')
            await sendMessage(transcript)
          } else {
            setStatusMsg('No speech detected — try again.')
            setTimeout(() => setStatusMsg(''), 2500)
          }
        } catch (err) {
          setStatusMsg(`STT failed: ${err.message}`)
          setTimeout(() => setStatusMsg(''), 3000)
        }
      }

      recorder.start()
      setIsRecording(true)
      setStatusMsg('🔴 Recording… release to send')
    } catch {
      setStatusMsg('Microphone permission denied.')
      setTimeout(() => setStatusMsg(''), 3000)
    }
  }, [isRecording, loading, sendMessage])

  // ── Keep the ref in sync with the latest startRecording ──────────────────
  useEffect(() => {
    startRecordingRef.current = startRecording
  }, [startRecording])

  // ── Stop voice recording ─────────────────────────────────────────────────
  const stopRecording = useCallback(() => {
    if (!isRecording || !mediaRecorderRef.current) return
    setIsRecording(false)
    if (mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
  }, [isRecording])

  // ── 🎙️ Wake Word SSE listener — runs once, always uses latest fn via ref ──
  useEffect(() => {
    let es = null
    let reconnectTimer = null

    function connect() {
      es = new EventSource(`${API_BASE}/api/wake-stream`)

      es.onopen = () => {
        console.log('🟢 Wake word stream connected')
        setWakeWordActive(true)
      }

      es.onmessage = (event) => {
        if (event.data === 'WAKE_DETECTED') {
          console.log('🎙️ "Hey Jarvis" detected — starting recording!')
          setStatusMsg('👂 Wake word detected — listening…')
          // Call through ref so we always have the fresh, non-stale version
          startRecordingRef.current?.()
        }
      }

      es.onerror = () => {
        // Server not up yet or connection dropped — retry in 5s
        setWakeWordActive(false)
        es?.close()
        reconnectTimer = setTimeout(connect, 5000)
      }
    }

    connect()

    return () => {
      es?.close()
      clearTimeout(reconnectTimer)
      setWakeWordActive(false)
    }
  }, [])   // ← intentionally empty: ref keeps startRecording fresh without re-subscribing

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Emotion dot color ────────────────────────────────────────────────────
  const emotionColor =
    status.current_emotion === 'angry' || status.current_emotion === 'stressed'
      ? 'bg-red-500'
      : status.current_emotion === 'sad'
      ? 'bg-blue-400'
      : 'bg-green-400'

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-200 overflow-hidden">

      {/* ══ Feature Matrix Overlay ══════════════════════════════════════════ */}
      {showFeatureMatrix && (
        <FeatureMatrix onClose={() => setShowFeatureMatrix(false)} />
      )}

      {/* ══ Header / HUD Bar ══════════════════════════════════════════════ */}
      <header className="flex justify-between items-center px-6 py-4 bg-slate-900/80 backdrop-blur border-b border-indigo-500/20 shrink-0 shadow-lg">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-xl font-bold shadow-[0_0_20px_rgba(124,58,237,0.5)]">
            J
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-[3px] text-cyan-400 leading-none">JARVIS OS</h1>
            <p className="text-[10px] text-slate-500 tracking-widest mt-0.5">VOICE INTELLIGENCE SYSTEM</p>
          </div>
        </div>

        {/* Live status chips + Capabilities button */}
        <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap justify-end">

          {/* ⬡ Capabilities toggle button */}
          <button
            id="capabilities-btn"
            onClick={() => setShowFeatureMatrix(true)}
            title="View Jarvis Capabilities"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-[11px] font-semibold tracking-wider hover:bg-indigo-500/20 hover:border-indigo-400/50 hover:text-indigo-200 transition-all duration-200 hover:shadow-[0_0_12px_rgba(99,102,241,0.25)] active:scale-95"
          >
            <span className="text-base leading-none">⬡</span>
            <span className="hidden sm:inline">CAPABILITIES</span>
          </button>

          {/* Wake word status indicator */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-medium tracking-wide transition-colors ${
              wakeWordActive
                ? 'bg-violet-900/40 border-violet-500/50 text-violet-300'
                : 'bg-slate-800/60 border-slate-700 text-slate-500'
            }`}
            title={wakeWordActive ? 'Listening for "Hey Jarvis"' : 'Wake word engine offline'}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${wakeWordActive ? 'bg-violet-400 animate-pulse' : 'bg-slate-600'}`} />
            {wakeWordActive ? '👂 Listening' : '● Offline'}
          </div>

          <span className="hidden sm:inline">
            🎯 <span className="text-slate-300">{status.current_focus}</span>
          </span>
          {status.tech_stack.length > 0 && (
            <span className="hidden md:inline text-slate-500">
              Stack: <span className="text-slate-300">{status.tech_stack.join(', ')}</span>
            </span>
          )}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700">
            <span className={`w-2 h-2 rounded-full animate-pulse ${emotionColor}`} />
            <span className="capitalize font-medium">
              {emotionEmoji[status.current_emotion] ?? '😐'} {status.current_emotion}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_6px_#4ade80]" />
            <span className="text-slate-300">{status.name}</span>
          </div>
        </div>
      </header>

      {/* ══ Chat Window ═══════════════════════════════════════════════════ */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex msg-enter ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'ai' && (
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-sm shrink-0 self-end mr-2">
                🤖
              </div>
            )}
            <div
              className={`max-w-[78%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-lg ${
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-violet-600 to-indigo-600 text-white rounded-br-sm'
                  : 'bg-slate-800/90 border border-indigo-500/20 text-slate-200 rounded-bl-sm backdrop-blur'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-sm shrink-0 self-end ml-2">
                👤
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex justify-start items-end gap-2 msg-enter">
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-sm shrink-0">
              🤖
            </div>
            <div className="bg-slate-800/90 border border-indigo-500/20 px-4 py-3 rounded-2xl rounded-bl-sm backdrop-blur">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* ══ Status message bar ════════════════════════════════════════════ */}
      {statusMsg && (
        <div className="text-center text-xs text-slate-400 py-1.5 bg-slate-900/60 shrink-0 tracking-wide border-t border-slate-800">
          {statusMsg}
        </div>
      )}

      {/* ══ Input Row ═════════════════════════════════════════════════════ */}
      <div className="flex items-end gap-2 px-4 py-4 border-t border-indigo-500/20 bg-slate-900/80 backdrop-blur shrink-0">
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Ask Jarvis… or say "Hey Jarvis" or hold 🎤'
          disabled={loading || isRecording}
          className="flex-1 bg-slate-800 border border-slate-700 focus:border-cyan-500 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none transition-colors outline-none disabled:opacity-50 leading-relaxed"
        />

        {/* Send button */}
        <button
          id="send-btn"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          title="Send (Enter)"
          className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white text-base flex items-center justify-center shadow-[0_2px_12px_rgba(124,58,237,0.4)] transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 shrink-0"
        >
          ➤
        </button>

        {/* Microphone button — hold to record */}
        <button
          id="mic-btn"
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onMouseLeave={stopRecording}
          onTouchStart={(e) => { e.preventDefault(); startRecording() }}
          onTouchEnd={(e) => { e.preventDefault(); stopRecording() }}
          disabled={loading}
          title={isRecording ? 'Release to transcribe' : 'Hold to speak'}
          className={`w-11 h-11 rounded-xl text-white text-lg flex items-center justify-center shadow-lg select-none transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shrink-0 ${
            isRecording
              ? 'bg-gradient-to-br from-red-600 to-red-500 animate-pulse pulse-ring'
              : 'bg-gradient-to-br from-violet-600 to-indigo-600 shadow-[0_2px_12px_rgba(124,58,237,0.4)]'
          }`}
        >
          🎤
        </button>
      </div>

      {/* ══ Footer hint ══════════════════════════════════════════════════ */}
      <div className="text-center text-[10px] text-slate-600 py-1.5 tracking-wide shrink-0">
        Say <kbd className="bg-slate-800 border border-slate-700 rounded px-1 text-violet-400">"Hey Jarvis"</kbd> to wake
        &nbsp;·&nbsp; Press <kbd className="bg-slate-800 border border-slate-700 rounded px-1 text-slate-400">Enter</kbd> to send
        &nbsp;·&nbsp; Hold <kbd className="bg-slate-800 border border-slate-700 rounded px-1 text-slate-400">🎤</kbd> to speak
        &nbsp;·&nbsp; Click <kbd className="bg-slate-800 border border-slate-700 rounded px-1 text-indigo-400">⬡</kbd> for capabilities
      </div>
    </div>
  )
}

export default App
