import sqlite3
import os
from datetime import datetime
from utils.logger import logger

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "commuflow.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assignee_openid TEXT DEFAULT '',
            assignee_name TEXT DEFAULT '',
            creator_openid TEXT DEFAULT '',
            creator_name TEXT DEFAULT '',
            due_date TEXT DEFAULT '',
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            completed_at TEXT,
            source_msg TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS roles (
            openid TEXT NOT NULL,
            role TEXT NOT NULL,
            scope TEXT DEFAULT 'global',
            chat_id TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(openid, role, scope, chat_id)
        );

        CREATE TABLE IF NOT EXISTS task_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            actor_openid TEXT DEFAULT '',
            action TEXT NOT NULL,
            old_status TEXT DEFAULT '',
            new_status TEXT DEFAULT '',
            payload_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()
    logger.info("task db initialized")


def add_task(title: str, assignee_openid: str, assignee_name: str,
             creator_openid: str, creator_name: str,
             due_date: str = "", description: str = "", source_msg: str = "") -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO tasks (title, assignee_openid, assignee_name, creator_openid, creator_name,
           due_date, description, source_msg)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, assignee_openid, assignee_name, creator_openid, creator_name,
         due_date, description, source_msg)
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_task(task_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_task_status(task_id: int, status: str) -> None:
    conn = get_conn()
    if status == "completed":
        conn.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                     (status, datetime.now().isoformat(), task_id))
    else:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()


def add_task_event(task_id: int, actor_openid: str, action: str,
                   old_status: str = "", new_status: str = "",
                   payload_json: str = "{}") -> None:
    conn = get_conn()
    conn.execute(
        """INSERT INTO task_events
           (task_id, actor_openid, action, old_status, new_status, payload_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (task_id, actor_openid, action, old_status, new_status, payload_json)
    )
    conn.commit()
    conn.close()


def add_role(openid: str, role: str, scope: str = "global", chat_id: str = "") -> None:
    conn = get_conn()
    conn.execute(
        """INSERT OR IGNORE INTO roles (openid, role, scope, chat_id)
           VALUES (?, ?, ?, ?)""",
        (openid, role, scope, chat_id)
    )
    conn.commit()
    conn.close()


def get_roles(openid: str, chat_id: str = "") -> list[str]:
    conn = get_conn()
    rows = conn.execute(
        """SELECT role FROM roles
           WHERE openid = ?
             AND (scope = 'global' OR chat_id = ?)
           ORDER BY role""",
        (openid, chat_id)
    ).fetchall()
    conn.close()
    return [r["role"] for r in rows]


def query_user_tasks(openid: str, status_filter: str = "") -> list[dict]:
    conn = get_conn()
    if status_filter:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE assignee_openid = ? AND status = ? ORDER BY created_at DESC",
            (openid, status_filter)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE assignee_openid = ? AND status != 'completed' ORDER BY created_at DESC",
            (openid,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_overdue_tasks() -> list[dict]:
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    rows = conn.execute(
        """SELECT * FROM tasks WHERE status IN ('pending', 'in_progress') AND due_date < ? ORDER BY due_date""",
        (now,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_tasks() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_task_by_title(title: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM tasks WHERE title LIKE ? ORDER BY created_at DESC LIMIT 1",
        (f"%{title}%",)
    ).fetchall()
    conn.close()
    return dict(row[0]) if row else None


init_db()
