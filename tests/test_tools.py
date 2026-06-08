"""L0: Tool layer tests — no LLM, just SQLite"""
import sys, io
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from utils.task_manager import init_db
from agent.tools import create_task, complete_task, verify_task, query_my_tasks, search_sop

init_db()

ASSIGNEE = "ou_assignee_001"
CREATOR = "ou_creator_001"

print("=== L0-1: create_task ===")
tid = create_task.invoke({"title": "竞品分析", "assignee_openid": ASSIGNEE, "creator_openid": CREATOR, "due_date": "2026-06-19"})
assert tid.isdigit(), f"FAIL: expected numeric ID, got {tid}"
print(f"  created: T{tid.zfill(3)}")

print("=== L0-2: query_my_tasks ===")
result = query_my_tasks.invoke({"user_openid": ASSIGNEE})
assert "竞品分析" in result, f"FAIL: task not found in {result}"
print(f"  found: {result[:80]}")

print("=== L0-3: complete_task ===")
tid2 = complete_task.invoke({"user_openid": ASSIGNEE, "task_id_or_title": tid})
assert tid2 == tid, f"FAIL: returned {tid2} != {tid}"
from utils.task_manager import get_task
t = get_task(int(tid))
assert t["status"] == "verified", f"FAIL: status={t['status']}"
print(f"  status: verified")

print("=== L0-4: verify_task ===")
tid3 = verify_task.invoke({"user_openid": CREATOR, "task_id_or_title": "T" + tid.zfill(3)})
assert tid3 == tid, f"FAIL: returned {tid3} != {tid}"
t = get_task(int(tid))
assert t["status"] == "completed", f"FAIL: status={t['status']}"
print(f"  status: completed")

print("=== L0-5: verify_task auto-find ===")
# Create another task, complete it, then verify without ID
tid4 = create_task.invoke({"title": "报告", "assignee_openid": ASSIGNEE, "creator_openid": CREATOR, "due_date": "2026-06-20"})
complete_task.invoke({"user_openid": ASSIGNEE, "task_id_or_title": tid4})
tid5 = verify_task.invoke({"user_openid": CREATOR, "task_id_or_title": ""})
assert tid5 == tid4, f"FAIL: auto-find returned {tid5} != {tid4}"
print(f"  auto-find: T{tid5.zfill(3)}")

print("=== L0-6: search_sop ===")
result = search_sop.invoke({"question": "紧急订单变更"})
assert "NO_RESULTS" not in result, f"FAIL: no results {result[:50]}"
print(f"  found: {result[:80]}...")

print("\nL0 ALL PASSED")