"""L2: 模拟飞书真实流程 —— 纯工具层测试（不需要LLM）"""
import sys, io, json
import sqlite3
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from utils.task_manager import init_db, get_task, get_all_tasks
from utils.task_manager import add_role, DB_PATH
from agent.tools import create_task, get_task_status, complete_task, verify_task, query_my_tasks

init_db()
conn = sqlite3.connect(DB_PATH)
for table in ("tasks", "roles", "task_events"):
    conn.execute(f"DELETE FROM {table}")
conn.commit()
conn.close()

CREATOR = "ou_xiaohai"
ASSIGNEE = "ou_user033075"
add_role(CREATOR, "creator")
add_role("ou_other_manager", "creator")

print("=" * 60)
print("场景模拟：飞书群聊中的完整任务闭环")
print("=" * 60)

# ─── 场景1：创建任务 ───
print("\n[场景1] 小海: @CommuFlow 请@用户033075 下周五18:00前完成竞品分析报告")
tid_raw = create_task.invoke({
    "title": "竞品分析报告",
    "assignee_openid": ASSIGNEE,
    "creator_openid": CREATOR,
    "due_date": "2026-06-19"
})
task_id = int(json.loads(tid_raw)["id"])
print(f"  创建成功 → T{task_id:03d}")
print(f"  回复应包含: 任务「竞品分析报告」已创建，责任人：用户033075，截止：2026-06-19，完成后请回复「T{task_id:03d} 已完成」")

# ─── 场景2：查询我的任务 ───
print(f"\n[场景2] 用户033075: @CommuFlow 我的任务有哪些")
result = query_my_tasks.invoke({"user_openid": ASSIGNEE})
tasks_list = json.loads(result)
assert len(tasks_list) > 0, "FAIL: no tasks found"
print(f"  查询到 {len(tasks_list)} 个任务:")
for t in tasks_list:
    print(f"    T{t['id']} [{t['status']}] {t['title']} 截止:{t['due_date']}")

# ─── 场景3：查看任务状态 ───
print(f"\n[场景3] 查询 T{task_id:03d} 状态")
status = get_task_status.invoke({"task_id_or_title": f"T{task_id:03d}"})
status_obj = json.loads(status)
assert status_obj["status"] == "pending", f"FAIL: expected pending, got {status_obj['status']}"
print(f"  状态: {status_obj['status']} (assignee={status_obj['assignee']})")

# ─── 场景4：完成任务 ───
print(f"\n[场景4] 用户033075: @CommuFlow 竞品分析报告 已完成")
tid2 = complete_task.invoke({"user_openid": ASSIGNEE, "task_id_or_title": "竞品分析报告"})
tid2 = json.loads(tid2)["id"]
assert int(tid2) == task_id, f"FAIL: complete returned {tid2}"
t = get_task(task_id)
assert t["status"] == "verified", f"FAIL: status={t['status']}"
print(f"  T{task_id:03d} 状态 → verified (待验收)")
print(f"  回复应包含: T{task_id:03d} 竞品分析报告 已标记待验收。请创建者回复验收通过。")

# ─── 场景5：验收通过（不给ID，自动匹配） ───
print(f"\n[场景5] 小海: @CommuFlow 验收通过")
tid3 = verify_task.invoke({"user_openid": CREATOR, "task_id_or_title": ""})
tid3 = json.loads(tid3)["id"]
assert int(tid3) == task_id, f"FAIL: auto-verify returned {tid3}, expected {task_id}"
t = get_task(task_id)
assert t["status"] == "completed", f"FAIL: status={t['status']}"
print(f"  T{task_id:03d} 状态 → completed (验收通过)")

# ─── 场景6：创建第二个任务，测试 verify 按 creator 精确匹配 ───
print(f"\n[场景6] 创建第二个任务（不同创建者模拟场景）")
tid7 = create_task.invoke({
    "title": "采购物料",
    "assignee_openid": ASSIGNEE,
    "creator_openid": "ou_other_manager",
    "due_date": "2026-06-20"
})
tid7 = int(json.loads(tid7)["id"])
complete_task.invoke({"user_openid": ASSIGNEE, "task_id_or_title": str(tid7)})
print(f"  T{tid7:03d} 采购物料 → verified (创建者=ou_other_manager)")

# 小海验收"验收通过"——应该找不到自己创建的verified任务（唯一的是别人的）
# 需要创建新任务给小海
tid8 = create_task.invoke({
    "title": "周报提交",
    "assignee_openid": ASSIGNEE,
    "creator_openid": CREATOR,
    "due_date": "2026-06-10"
})
tid8 = int(json.loads(tid8)["id"])
complete_task.invoke({"user_openid": ASSIGNEE, "task_id_or_title": str(tid8)})
print(f"  T{tid8:03d} 周报提交 → verified (创建者=小海)")

# 现在小海验收
tid9 = verify_task.invoke({"user_openid": CREATOR, "task_id_or_title": ""})
tid9 = json.loads(tid9)["id"]
assert int(tid9) == tid8, f"FAIL: auto-verify should pick T{tid8:03d} (creator match), got T{int(tid9):03d}"
t = get_task(tid8)
assert t["status"] == "completed"
print(f"  T{tid8:03d} → completed (按creator精确匹配)")

# ─── 场景7：get_task_status 查不到 ───
print(f"\n[场景7] 查询不存在的任务")
result = get_task_status.invoke({"task_id_or_title": "T999"})
assert result == "NOT_FOUND", f"FAIL: expected NOT_FOUND, got {result}"
print(f"  T999 → NOT_FOUND ✓")

# ─── 总结 ───
print("\n" + "=" * 60)
print("全部场景通过！")
print("=" * 60)
print("\nDB 最终状态:")
for t in get_all_tasks():
    print(f"  T{t['id']:03d} [{t['status']}] {t['title']} → assignee={t['assignee_openid']} creator={t['creator_openid']}")
