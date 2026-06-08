"""Feishu-spec simulation test — matches actual API format from docs"""
import sys, io, json, re
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db, get_all_tasks

init_db()
CHAT = "oc_test"

CREATOR = "ou_creator_real_001"
ASSIGNEE = "ou_assignee_real_002"
BOT = "ou_bot_003"

def sim_feishu(raw_text, sender_openid):
    """
    Simulate what main.py does with real Feishu format.
    Text contains @_user_1 for bot, @_user_2 for assignee.
    """
    # Build mentions per Feishu API spec: id is string, not nested object
    mentions = [
        {"key": "@_user_1", "id": BOT, "name": "CommuFlow"},
        {"key": "@_user_2", "id": ASSIGNEE, "name": "user_033075"},
    ]
    mention_map = {}
    for m in mentions:
        mention_map[m["key"]] = {"name": m["name"], "open_id": m["id"]}

    text = raw_text
    for key, info in mention_map.items():
        text = text.replace(key, f"@{info['name']}")

    return run_agent(
        user_id=sender_openid,
        chat_id=CHAT,
        text=text,
        mention_map=mention_map
    )

clear_history(CHAT)

# ═══════════════════════════════════
print("=" * 60)
print("STEP 1: Create task")
print("=" * 60)
r = sim_feishu("@_user_1 @_user_2 next Friday 18:00 finish market analysis", CREATOR)
print("REPLY:", r[:200])
tid = re.search(r"T\d{3}", r)
assert tid, "FAIL: no task ID"
task_id = tid.group()
print(f"TASK: {task_id}")

# ═══════════════════════════════════
print("\n" + "=" * 60)
print("STEP 2: Query progress")
print("=" * 60)
r = sim_feishu("@_user_1 my tasks", ASSIGNEE)
print("REPLY:", r[:200])
assert task_id in r, "FAIL: task not visible"

# ═══════════════════════════════════
print("\n" + "=" * 60)
print("STEP 3: Complete task")
print("=" * 60)
r = sim_feishu(f"@_user_1 {task_id} done", ASSIGNEE)
print("REPLY:", r[:200])
assert "待验收" in r, "FAIL: not marked verified"

# ═══════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4: Verify task")
print("=" * 60)
r = sim_feishu(f"@_user_1 {task_id} accept", CREATOR)
print("REPLY:", r[:200])
assert "闭环" in r or "验收通过" in r, "FAIL: verification failed"

# ═══════════════════════════════════
print("\n" + "=" * 60)
print("STEP 5: DB state")
print("=" * 60)
for t in get_all_tasks():
    print(f"  T{t['id']} [{t['status']}] {t['title']} assignee={t['assignee_openid']}")
    assert t['assignee_openid'] == ASSIGNEE, f"FAIL: wrong open_id {t['assignee_openid']}"
    assert t['status'] == 'completed', f"FAIL: not completed, got {t['status']}"

print("\n" + "=" * 60)
print("ALL 5 STEPS PASSED")
print("=" * 60)