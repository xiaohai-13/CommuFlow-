"""Task detail query tests."""
import io
import json
import sqlite3
import sys

sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.schemas import TaskAction
from agent.task_agent import _execute_step
from agent.tools import create_task, get_task_detail
from utils.task_manager import DB_PATH, add_role, init_db


def reset_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    for table in ("tasks", "roles", "task_events"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


def as_json(value: str) -> dict:
    return json.loads(value)


CREATOR = "ou_creator"
ASSIGNEE = "ou_assignee"
OTHER = "ou_other"

reset_db()
add_role(CREATOR, "creator")

print("=== D1: create task fixture ===")
task = as_json(create_task.invoke({
    "title": "竞品分析报告",
    "assignee_openid": ASSIGNEE,
    "creator_openid": CREATOR,
    "due_date": "2026-06-19",
}))
task_id = task["id"]
print(f"  OK: created T{task_id}")

print("=== D2: creator can query by ID ===")
detail = as_json(get_task_detail.invoke({
    "user_openid": CREATOR,
    "task_id_or_title": f"T{task_id}",
}))
assert detail["id"] == task_id, detail
assert detail["title"] == "竞品分析报告", detail
print("  OK: detail by ID")

print("=== D3: assignee can query by title ===")
detail = as_json(get_task_detail.invoke({
    "user_openid": ASSIGNEE,
    "task_id_or_title": "竞品分析报告",
}))
assert detail["id"] == task_id, detail
print("  OK: detail by title")

print("=== D4: unrelated user cannot query detail ===")
detail = as_json(get_task_detail.invoke({
    "user_openid": OTHER,
    "task_id_or_title": f"T{task_id}",
}))
assert detail["error"] == "UNAUTHORIZED", detail
print("  OK: unauthorized detail blocked")

print("=== D5: ambiguous title returns candidates ===")
task2 = as_json(create_task.invoke({
    "title": "竞品分析报告-二期",
    "assignee_openid": ASSIGNEE,
    "creator_openid": CREATOR,
    "due_date": "2026-06-20",
}))
detail = as_json(get_task_detail.invoke({
    "user_openid": CREATOR,
    "task_id_or_title": "竞品分析报告",
}))
assert detail["error"] == "AMBIGUOUS", detail
assert len(detail["candidates"]) == 2, detail
print("  OK: ambiguous detail asks for task ID")

print("=== D6: TaskAgent detail reply ===")
reply = _execute_step(
    TaskAction(action="detail", task_id=f"T{task_id}"),
    CREATOR,
    {},
)
assert f"T{task_id}" in reply, reply
assert "状态:" in reply, reply
print("  OK: agent detail reply")

print("\nTASK DETAIL TESTS PASSED")
