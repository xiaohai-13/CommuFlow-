import sqlite3
from datetime import datetime
from db.database import get_db


def next_task_id() -> str:
    db = get_db()
    cur = db.execute("UPDATE task_counter SET seq = seq + 1 WHERE id = 1 RETURNING seq")
    seq = cur.fetchone()[0]
    db.commit()
    return f"T{seq:03d}"


def create_task(title: str, assignee_openid: str, assignee_name: str,
                creator_openid: str, creator_name: str,
                due_date: str = "", description: str = "",
                source_msg: str = "") -> dict:
    task_id = next_task_id()
    db = get_db()
    db.execute(
        """INSERT INTO tasks (id, title, description, assignee_openid, assignee_name,
           creator_openid, creator_name, due_date, source_msg)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (task_id, title, description, assignee_openid, assignee_name,
         creator_openid, creator_name, due_date, source_msg)
    )
    db.commit()
    return get_task(task_id)


def get_task(task_id: str) -> dict | None:
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def update_task_status(task_id: str, status: str) -> dict | None:
    db = get_db()
    if status == "已完成":
        db.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), task_id)
        )
    else:
        db.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    db.commit()
    return get_task(task_id)


def query_user_tasks(openid: str, status_filter: str = "") -> list[dict]:
    db = get_db()
    if status_filter:
        rows = db.execute(
            "SELECT * FROM tasks WHERE assignee_openid = ? AND status = ? ORDER BY created_at DESC",
            (openid, status_filter)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM tasks WHERE assignee_openid = ? AND status != '已完成' ORDER BY created_at DESC",
            (openid,)
        ).fetchall()
    return [dict(r) for r in rows]


def query_overdue_tasks() -> list[dict]:
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    rows = db.execute(
        """SELECT * FROM tasks
           WHERE status IN ('pending', '进行中')
           AND due_date < ?
           ORDER BY due_date""",
        (now,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_task_by_id_or_title(query: str) -> dict | None:
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (query,)).fetchone()
    if row:
        return dict(row)
    rows = db.execute("SELECT * FROM tasks WHERE title LIKE ? ORDER BY created_at DESC LIMIT 1",
                      (f"%{query}%",)).fetchall()
    return dict(rows[0]) if rows else None
