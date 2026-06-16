import os
import uuid
import requests
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# ─── Ollama Embedding Configuration ──────────────────────────────────────────
# Uses nomic-embed-text which produces 768-dimensional vectors.
# Make sure to pull it first: `ollama pull nomic-embed-text`
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
EMBED_DIM = 768   # nomic-embed-text outputs 768 dimensions

# ─── Pinecone Configuration ───────────────────────────────────────────────────
_pinecone_key = os.getenv("PINECONE_API_KEY")
if not _pinecone_key:
    raise EnvironmentError("PINECONE_API_KEY is not set in the environment.")

pc = Pinecone(api_key=_pinecone_key)

INDEX_NAME = "assistant-memory-local"   # New index name (768-dim, different from the Gemini 3072-dim one)

def setup_pinecone():
    """Creates the Pinecone index if it doesn't exist yet, then returns it."""
    existing = pc.list_indexes().names()
    if INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{INDEX_NAME}' (768-dim for nomic-embed-text)...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",  # Default free-tier region
            ),
        )
        print("Index created successfully!")
    return pc.Index(INDEX_NAME)

# Get the active index at module load time
index = setup_pinecone()

def _embed(text: str) -> list:
    """
    Helper: converts text to an embedding vector using Ollama's local nomic-embed-text model.
    Calls the Ollama /api/embeddings endpoint directly.
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
            "Make sure Ollama is running (`ollama serve`) and nomic-embed-text is pulled "
            "(`ollama pull nomic-embed-text`)."
        )
    except Exception as e:
        raise RuntimeError(f"Embedding error: {e}")

def remember_this(text: str, category: str = "general"):
    """Converts text to a local vector and saves it to Pinecone."""
    try:
        vector = _embed(text)
        doc_id = str(uuid.uuid4())
        index.upsert(vectors=[{
            "id": doc_id,
            "values": vector,
            "metadata": {"text": text, "category": category},
        }])
        print(f"💾 Memory saved: {text[:50]}...")
    except Exception as e:
        print(f"[Error saving memory]: {e}")

def recall(query: str, top_k: int = 2) -> str:
    """Searches Pinecone for memories related to the query."""
    try:
        query_vector = _embed(query)
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )
        memories = [
            match["metadata"]["text"]
            for match in results.get("matches", [])
            if match.get("metadata")
        ]
        return "\n".join(memories) if memories else "No relevant past memories found."
    except Exception as e:
        return f"[Error recalling memory]: {e}"

if __name__ == "__main__":
    print(f"🧠 Vector Memory Online — using Ollama ({EMBED_MODEL}) + Pinecone.")
    # Test saving a memory
    remember_this(
        "When starting a Spring Boot project, Ashen prefers to use MongoDB for the database.",
        category="tech_preference",
    )

    # Test recalling a memory
    print("\n🔍 Recalling...")
    past_knowledge = recall("What database do I use with Spring Boot?")
    print(f"Result: {past_knowledge}")