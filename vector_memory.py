import os
import uuid
from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Initialize the Gemini client — GEMINI_API_KEY is picked up automatically by the SDK.
# Pass it explicitly here as a safety net for all environments.
_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not _gemini_key:
    raise EnvironmentError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in the environment.")

ai_client = genai.Client(api_key=_gemini_key)

_pinecone_key = os.getenv("PINECONE_API_KEY")
if not _pinecone_key:
    raise EnvironmentError("PINECONE_API_KEY is not set in the environment.")

pc = Pinecone(api_key=_pinecone_key)

INDEX_NAME = "assistant-memory"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 3072   # gemini-embedding-001 outputs 3072 dimensions

def setup_pinecone():
    """Creates the Pinecone index if it doesn't exist yet, then returns it."""
    existing = pc.list_indexes().names()
    if INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{INDEX_NAME}' (this takes about 60 seconds)...")
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
    """Helper: converts text to a Gemini embedding vector."""
    response = ai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
    )
    return response.embeddings[0].values

def remember_this(text: str, category: str = "general"):
    """Converts text to a vector and saves it to Pinecone."""
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
    print("🧠 Vector Memory Online.")
    # Test saving a memory
    remember_this(
        "When starting a Spring Boot project, Ashen prefers to use MongoDB for the database.",
        category="tech_preference",
    )

    # Test recalling a memory
    print("\n🔍 Recalling...")
    past_knowledge = recall("What database do I use with Spring Boot?")
    print(f"Result: {past_knowledge}")