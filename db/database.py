import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")


def get_db():
    return conn


def init_db():
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS tasks (
            id              TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            description     TEXT DEFAULT '',
            assignee_openid TEXT NOT NULL,
            assignee_name   TEXT DEFAULT '',
            creator_openid  TEXT NOT NULL,
            creator_name    TEXT DEFAULT '',
            due_date        TEXT,
            status          TEXT DEFAULT 'pending',
            completed_at    TEXT,
            source_msg      TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS task_counter (
            id INTEGER PRIMARY KEY,
            seq INTEGER DEFAULT 0
        );

        INSERT OR IGNORE INTO task_counter (id, seq) VALUES (1, 0);
    ''')
    conn.commit()
