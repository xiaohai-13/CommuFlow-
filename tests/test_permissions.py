"""Permission layer tests: admin, creator, assignee."""
import io
import json
import sqlite3
import sys

sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.tools import create_task, complete_task, verify_task, get_task_detail
from utils.task_manager import DB_PATH, add_role, get_task, init_db


def reset_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    for table in ("tasks", "roles", "task_events"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


def as_json(value: str) -> dict:
    return json.loads(value)


ADMIN = "ou_admin"
CREATOR = "ou_creator"
ASSIGNEE = "ou_assignee"
OTHER = "ou_other"


reset_db()
add_role(ADMIN, "admin")
add_role(CREATOR, "creator")

print("=== P1: non-creator cannot create task ===")
result = as_json(create_task.invoke({
    "title": "竞品分析报告",
    "assignee_openid": ASSIGNEE,
    "creator_openid": OTHER,
    "due_date": "2026-06-19",
}))
assert result["error"] == "UNAUTHORIZED", result
print("  OK: unauthorized create blocked")

print("=== P2: creator role can create task ===")
result = as_json(create_task.invoke({
    "title": "竞品分析报告",
    "assignee_openid": ASSIGNEE,
    "creator_openid": CREATOR,
    "due_date": "2026-06-19",
}))
task_id = result["id"]
assert task_id.isdigit(), result
print(f"  OK: task created T{task_id}")

print("=== P3: non-assignee cannot complete task ===")
result = as_json(complete_task.invoke({
    "user_openid": OTHER,
    "task_id_or_title": f"T{task_id}",
}))
assert result["error"] == "UNAUTHORIZED", result
print("  OK: unauthorized complete blocked")

print("=== P4: assignee can complete task ===")
result = as_json(complete_task.invoke({
    "user_openid": ASSIGNEE,
    "task_id_or_title": f"T{task_id}",
}))
assert result["status"] == "verified", result
assert get_task(int(task_id))["status"] == "verified"
print("  OK: assignee marked task verified")

print("=== P5: non-creator cannot verify task ===")
result = as_json(verify_task.invoke({
    "user_openid": OTHER,
    "task_id_or_title": f"T{task_id}",
}))
assert result["error"] == "UNAUTHORIZED", result
print("  OK: unauthorized verify blocked")

print("=== P6: creator can verify task ===")
result = as_json(verify_task.invoke({
    "user_openid": CREATOR,
    "task_id_or_title": f"T{task_id}",
}))
assert result["status"] == "completed", result
assert get_task(int(task_id))["status"] == "completed"
print("  OK: creator verified task")

print("=== P7: detail visibility ===")
creator_detail = as_json(get_task_detail.invoke({
    "user_openid": CREATOR,
    "task_id_or_title": f"T{task_id}",
}))
assert creator_detail["id"] == task_id, creator_detail
other_detail = as_json(get_task_detail.invoke({
    "user_openid": OTHER,
    "task_id_or_title": f"T{task_id}",
}))
assert other_detail["error"] == "UNAUTHORIZED", other_detail
admin_detail = as_json(get_task_detail.invoke({
    "user_openid": ADMIN,
    "task_id_or_title": f"T{task_id}",
}))
assert admin_detail["id"] == task_id, admin_detail
print("  OK: detail permissions enforced")

print("\nPERMISSION TESTS PASSED")
