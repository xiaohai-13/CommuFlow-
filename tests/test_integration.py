"""L2+L3: Agent + Integration test — full multi-agent pipeline"""
import sys, io, re
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db, get_all_tasks

init_db()
CHAT = "oc_test_multi"
clear_history(CHAT)

CREATOR = "ou_creator_001"
ASSIGNEE = "ou_assignee_002"
MENTIONS = {"@_user_2": {"name": "userB", "open_id": ASSIGNEE}}

def send(text, user, mentions=None):
    return run_agent(user, CHAT, text, mentions or {})

failed = []

# ── TASK LIFECYCLE ──
print("=" * 50)
print("L2-1: Task Agent — create")
print("=" * 50)
r = send("请@userB 下周五18:00前完成竞品分析报告", CREATOR, MENTIONS)
print("REPLY:", r[:150])
tid = re.search(r"T\d{3}", r)
if not tid:
    failed.append("L2-1: no task ID in reply")
else:
    task_id = tid.group()
    print(f"ID: {task_id}")

print("\n" + "=" * 50)
print("L2-2: Task Agent — query")
print("=" * 50)
r = send("我的任务有哪些", ASSIGNEE)
print("REPLY:", r[:150])
if task_id and task_id not in r:
    failed.append(f"L2-2: {task_id} not visible")

print("\n" + "=" * 50)
print("L2-3: Task Agent — complete")
print("=" * 50)
r = send(f"{task_id} 已完成", ASSIGNEE)
print("REPLY:", r[:150])
if task_id and task_id not in r:
    failed.append(f"L2-3: {task_id} not in complete reply")

print("\n" + "=" * 50)
print("L2-4: Task Agent — verify")
print("=" * 50)
r = send(f"{task_id} 验收通过", CREATOR)
print("REPLY:", r[:150])

# ── KNOWLEDGE ──
print("\n" + "=" * 50)
print("L2-5: Knowledge Agent")
print("=" * 50)
r = send("紧急订单变更流程是什么", CREATOR)
print("REPLY:", r[:150])
if "生产部" not in r and "production" not in r.lower() and "未找到" not in r:
    failed.append("L2-5: knowledge response seems wrong")

# ── CHAT FALLBACK ──
print("\n" + "=" * 50)
print("L2-6: Chat fallback")
print("=" * 50)
r = send("今天天气怎么样", CREATOR)
print("REPLY:", r[:100])

# ── DB VERIFY ──
print("\n" + "=" * 50)
print("DB state:")
print("=" * 50)
for t in get_all_tasks():
    print(f"  T{t['id']} [{t['status']}] {t['title']} -> {t['assignee_openid']}")

# ── RESULT ──
print("\n" + "=" * 50)
if failed:
    print(f"FAILED: {len(failed)} tests")
    for f in failed:
        print(f"  - {f}")
else:
    print("ALL TESTS PASSED")
print("=" * 50)