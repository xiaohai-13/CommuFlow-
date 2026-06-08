"""Simulate full Feishu flow — test mention_map resolution end-to-end"""
import sys, io, json
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db, get_all_tasks

init_db()

# Simulate what main.py does
CREATOR_OPENID = "ou_creator_real_abc"
ASSIGNEE_OPENID = "ou_assignee_real_xyz"
CHAT = "test_feishu_flow"

clear_history(CHAT)

def feishu_simulate(raw_text, sender_openid, raw_mentions):
    """Simulate main.py: parse mentions, replace @_user_X, call run_agent"""
    mention_map = {}
    for m in raw_mentions:
        key = m["key"]
        mention_map[key] = {"name": m["name"], "open_id": m["open_id"]}

    text = raw_text
    for key, info in mention_map.items():
        text = text.replace(key, f"@{info['name']}")

    return run_agent(
        user_id=sender_openid,
        chat_id=CHAT,
        text=text,
        mention_map=mention_map
    )

# === STEP 1: Creator assigns task with @mention ===
print("=" * 60)
print("STEP 1: Creator assigns task")
print("=" * 60)
r1 = feishu_simulate(
    raw_text="@_user_1 请@_user_2 下周五18:00前完成竞品分析报告",
    sender_openid=CREATOR_OPENID,
    raw_mentions=[
        {"key": "@_user_1", "name": "CommuFlow", "open_id": "ou_bot"},
        {"key": "@_user_2", "name": "用户033075", "open_id": ASSIGNEE_OPENID},
    ]
)
print(f"A: {r1[:200]}")

# === STEP 2: Assignee queries progress ===
print("\n" + "=" * 60)
print("STEP 2: Assignee queries progress")
print("=" * 60)
r2 = feishu_simulate(
    raw_text="@_user_1 我的任务有哪些",
    sender_openid=ASSIGNEE_OPENID,
    raw_mentions=[
        {"key": "@_user_1", "name": "CommuFlow", "open_id": "ou_bot"},
    ]
)
print(f"A: {r2[:200]}")

# === STEP 3: Check database correctness ===
print("\n" + "=" * 60)
print("STEP 3: Verify DB records")
print("=" * 60)
for t in get_all_tasks():
    print(f"  T{t['id']} title={t['title']} assignee_openid={t['assignee_openid']} status={t['status']}")
    if t['assignee_openid'] == ASSIGNEE_OPENID:
        print("  -> CORRECT open_id assigned")
    else:
        print(f"  -> WRONG open_id! Got {t['assignee_openid']}, expected {ASSIGNEE_OPENID}")

# === STEP 4: Assignee completes task ===
print("\n" + "=" * 60)
print("STEP 4: Assignee completes task")
print("=" * 60)
r3 = feishu_simulate(
    raw_text="@_user_1 竞品分析报告 已完成",
    sender_openid=ASSIGNEE_OPENID,
    raw_mentions=[{"key": "@_user_1", "name": "CommuFlow", "open_id": "ou_bot"}]
)
print(f"A: {r3[:200]}")

# === STEP 5: Creator verifies ===
print("\n" + "=" * 60)
print("STEP 5: Creator verifies")
print("=" * 60)
r4 = feishu_simulate(
    raw_text="@_user_1 验收通过",
    sender_openid=CREATOR_OPENID,
    raw_mentions=[{"key": "@_user_1", "name": "CommuFlow", "open_id": "ou_bot"}]
)
print(f"A: {r4[:200]}")

# === FINAL CHECK ===
print("\n" + "=" * 60)
print("FINAL: All tasks status")
print("=" * 60)
all_ok = True
for t in get_all_tasks():
    ok = t['assignee_openid'] == ASSIGNEE_OPENID
    if not ok: all_ok = False
    print(f"  T{t['id']} [{t['status']}] {t['title']} -> {t['assignee_openid']} {'OK' if ok else 'FAIL'}")

print(f"\n{'ALL PASSED' if all_ok else 'SOME FAILED'}")