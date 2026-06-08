import os
import cv2
import time
from dotenv import load_dotenv
from deepface import DeepFace
from pymongo import MongoClient

load_dotenv()

# Connect to your existing MongoDB memory with a timeout
mongo_client = MongoClient(
    os.getenv("MONGODB_URI"),
    serverSelectionTimeoutMS=5000,
)
db = mongo_client["assistant_memory"]
profile_collection = db["user_profile"]

# Consecutive failure counter — back off if camera/DeepFace keeps failing
_consecutive_failures = 0
_MAX_FAILURES = 5
_FAIL_BACKOFF_SECS = 15   # Sleep longer if things are broken

def update_db_emotion(emotion: str):
    """Updates your MongoDB profile with your current emotional state."""
    try:
        profile_collection.update_one(
            {"name": "Ashen"},
            {"$set": {"current_emotion": emotion}},
            upsert=True,
        )
        print(f"🧠 Memory Updated: Ashen is currently feeling {emotion}.")
    except Exception as e:
        print(f"[Warning] Could not update emotion in MongoDB: {e}")

def start_emotion_tracker():
    """Captures webcam frames periodically and analyzes facial expressions."""
    global _consecutive_failures

    # Index 0 is typically the built-in laptop webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return

    print("👁️ Emotion Tracker Online. Press Ctrl+C in terminal to stop.")

    try:
        while True:
            # Clear the buffer to ensure we get the most recent frame, not a delayed one
            cap.grab()
            ret, frame = cap.read()

            if not ret:
                print("Failed to grab frame. Retrying in 5 seconds...")
                time.sleep(5)
                continue

            try:
                # Analyze the frame using DeepFace
                # enforce_detection=False prevents crashes if you turn your head away
                result = DeepFace.analyze(
                    img_path=frame,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )

                # DeepFace can return a list if multiple faces are found; take the first
                if isinstance(result, list):
                    result = result[0]

                dominant_emotion = result["dominant_emotion"]
                update_db_emotion(dominant_emotion)
                _consecutive_failures = 0   # Reset failure counter on success

            except Exception as e:
                _consecutive_failures += 1
                print(f"Analysis skipped this cycle ({_consecutive_failures} failures): {e}")

                # If failures accumulate, back off longer to reduce CPU waste
                if _consecutive_failures >= _MAX_FAILURES:
                    print(f"[Warning] Too many failures. Backing off for {_FAIL_BACKOFF_SECS}s...")
                    time.sleep(_FAIL_BACKOFF_SECS)
                    _consecutive_failures = 0
                    continue

            # Sleep for 5 seconds to keep CPU/GPU usage incredibly low
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nEmotion tracker shutting down...")
    finally:
        # Always release the camera hardware cleanly
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_emotion_tracker()