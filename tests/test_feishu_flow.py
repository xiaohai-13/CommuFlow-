# -*- coding: utf-8 -*-
import sys, io, json, re
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db, get_all_tasks

init_db()
clear_history("test_feishu_flow")

CREATOR = "ou_creator_001"
ASSIGNEE = "ou_assignee_002"
CHAT = "test_feishu_flow"

def simulate(raw_text, sender, mentions_raw):
    mm = {}
    for m in mentions_raw:
        mm[m["key"]] = {"name": m["name"], "open_id": m["open_id"]}
    text = raw_text
    for k, v in mm.items():
        text = text.replace(k, "@" + v["name"])
    text = re.sub(r"@CommuFlow\s*", "", text).strip()
    return run_agent(user_id=sender, chat_id=CHAT, text=text, mention_map=mm)

MENTIONS_2 = [
    {"key": "@_user_1", "name": "CommuFlow", "open_id": "ou_bot"},
    {"key": "@_user_2", "name": "user_033075", "open_id": ASSIGNEE},
]
MENTIONS_1 = [{"key": "@_user_1", "name": "CommuFlow", "open_id": "ou_bot"}]

print("STEP1: create task")
r = simulate("@_user_1 qing @_user_2 next Friday 18:00 finish market analysis", CREATOR, MENTIONS_2)
print("  " + r[:150])
assert "market" in r.lower() or "analysis" in r.lower(), "should create task"

print("STEP2: query progress")
r = simulate("@_user_1 my tasks", ASSIGNEE, MENTIONS_1)
print("  " + r[:150])
assert "market" in r.lower() or "analysis" in r.lower(), "should see task"

print("STEP3: complete task")
r = simulate("@_user_1 market analysis done", ASSIGNEE, MENTIONS_1)
print("  " + r[:150])

print("STEP4: verify")
r = simulate("@_user_1 accept done", CREATOR, MENTIONS_1)
print("  " + r[:150])

print("FINAL:")
for t in get_all_tasks():
    tid = t["id"]
    ts = t["status"]
    tt = t["title"]
    ta = t["assignee_openid"]
    print("  T" + str(tid) + " [" + ts + "] " + tt + " -> " + ta)

print("DONE")
