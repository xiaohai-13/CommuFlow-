"""Conversation memory — SQLite-backed per-chat_id history"""
import sqlite3
import json
import os
from datetime import datetime
from utils.logger import logger

MEMORY_DB = os.path.join(os.path.dirname(__file__), "..", "data", "memory.db")
os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)


def get_conn():
    conn = sqlite3.connect(MEMORY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            entities_json TEXT DEFAULT '{}',
            intent TEXT DEFAULT '',
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_id ON conversations(chat_id)")
    conn.commit()
    conn.close()
    logger.info("memory db initialized")


def save_message(chat_id: str, role: str, content: str,
                 entities: dict = None, intent: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO conversations (chat_id, role, content, entities_json, intent) VALUES (?, ?, ?, ?, ?)",
        (chat_id, role, content, json.dumps(entities or {}, ensure_ascii=False), intent)
    )
    conn.commit()
    conn.close()


def load_history(chat_id: str, limit: int = 10) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content, entities_json, intent, timestamp FROM conversations WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_last_intent(chat_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT intent, entities_json FROM conversations WHERE chat_id = ? AND intent != '' ORDER BY id DESC LIMIT 1",
        (chat_id,)
    ).fetchone()
    conn.close()
    if row and row["intent"]:
        return {"intent": row["intent"], "entities": json.loads(row["entities_json"])}
    return None


def clear_history(chat_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


init_memory()