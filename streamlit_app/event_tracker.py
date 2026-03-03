import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "events.jsonl"


def log_event(session_id: str, user_id: str, page_name: str, event_type: str, metadata: dict = None):
    event = {
        "session_id": session_id,
        "user_id": user_id,
        "page_name": page_name,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata or {},
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
