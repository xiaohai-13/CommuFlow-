"""Multi-agent integration test"""
import sys, io, re
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db, get_all_tasks, add_role

init_db()
CHAT = "oc_test_multi"
clear_history(CHAT)

CREATOR = "ou_creator"
ASSIGNEE = "ou_assignee"
MENTIONS = {"@_user_2": {"name": "userB", "open_id": ASSIGNEE}}
add_role(CREATOR, "creator")

def send(text, user, mentions=None):
    return run_agent(user, CHAT, text, mentions or {})

failed = []
task_id = None

# ── CREATE ──
print("=" * 50 + "\nL2-1: TaskAgent — create\n" + "=" * 50)
r = send("请@userB 下周五18:00前完成竞品分析报告", CREATOR, MENTIONS)
print("REPLY:", r[:200])
tid = re.search(r"T\d{3}", r)
if tid:
    task_id = tid.group()
    print(f"TASK ID: {task_id}")
else:
    failed.append("L2-1: no T00X in reply")

# ── QUERY ──
if task_id:
    print("\n" + "=" * 50 + "\nL2-2: TaskAgent — query\n" + "=" * 50)
    r = send("我的任务有哪些", ASSIGNEE)
    print("REPLY:", r[:200])
    if task_id not in r:
        failed.append(f"L2-2: {task_id} not visible")

# ── COMPLETE ──
if task_id:
    print("\n" + "=" * 50 + "\nL2-3: TaskAgent — complete\n" + "=" * 50)
    r = send(f"{task_id} 已完成", ASSIGNEE)
    print("REPLY:", r[:200])
    if task_id not in r:
        failed.append(f"L2-3: {task_id} not in reply")

# ── VERIFY ──
if task_id:
    print("\n" + "=" * 50 + "\nL2-4: TaskAgent — verify\n" + "=" * 50)
    r = send(f"{task_id} 验收通过", CREATOR)
    print("REPLY:", r[:200])

# ── KNOWLEDGE ──
print("\n" + "=" * 50 + "\nL2-5: KnowledgeAgent\n" + "=" * 50)
r = send("紧急订单变更流程是什么", CREATOR)
print("REPLY:", r[:200])

# ── CHAT ──
print("\n" + "=" * 50 + "\nL2-6: Chat fallback\n" + "=" * 50)
r = send("今天天气怎么样", CREATOR)
print("REPLY:", r[:100])

# ── DB ──
print("\n" + "=" * 50 + "\nDB state:\n" + "=" * 50)
for t in get_all_tasks():
    print(f"  T{t['id']} [{t['status']}] {t['title']} -> {t['assignee_openid']}")

# ── RESULT ──
print("\n" + "=" * 50)
if failed:
    print(f"FAILED: {len(failed)}")
    for f in failed:
        print(f"  - {f}")
else:
    print("ALL TESTS PASSED")
print("=" * 50)
