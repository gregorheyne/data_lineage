import json
from datetime import datetime
from pathlib import Path

from streamlit_app.utils.db_connections import ensure_event_table_exists, get_pyodbc_connection, SCHEMA_NAME, TABLE_NAME

LOG_FILE = Path(__file__).parent.parent / "data" / "events.jsonl"


def upload_event(event: dict):
    ensure_event_table_exists()
    conn = get_pyodbc_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO [{SCHEMA_NAME}].[{TABLE_NAME}]"
        " (session_id, timestamp, user_id, page_name, event_type, metadata)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        event["session_id"],
        event["timestamp"],
        event["user_id"],
        event["page_name"],
        event["event_type"],
        json.dumps(event["metadata"]),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return None

def log_event(session_id: str, user_id: str, page_name: str, event_type: str, metadata: dict = None):
    event = {
        "session_id": session_id,
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "page_name": page_name,
        "event_type": event_type,
        "metadata": metadata or {},
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event | {"timestamp": event["timestamp"].isoformat()}) + "\n")
    try:
        1==1
        # upload_event(event)
    except Exception as e:
        print(f"[event_tracker] Azure SQL upload failed: {e}")

    return None