import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "events.jsonl"


def log_event(user_id: str, session_id: str, event_type: str, metadata: dict = None):
    event = {
        "user_id": user_id,
        "session_id": session_id,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata or {},
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
