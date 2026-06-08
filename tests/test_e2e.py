# End-to-end multi-user workflow test
import sys, io; sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from agent.graph import run_agent
from utils.task_manager import get_all_tasks, init_db

init_db()

CREATOR = "ou_creator_001"
ASSIGNEE = "ou_zhangsan_001"

print("=== Step 1: Creator assigns task ===")
r1 = run_agent(CREATOR, "chat_test", "请@张三 下周五前完成竞品分析报告，包含市场规模对比")
print(f"  -> {r1[:120]}")

print("\n=== Step 2: Creator provides due date ===")
r2 = run_agent(CREATOR, "chat_test", "请@张三 2026-06-15前完成竞品分析报告，包含市场规模对比")
print(f"  -> {r2[:150]}")

print("\n=== Step 3: Assignee queries progress ===")
r3 = run_agent(ASSIGNEE, "chat_test", "我的任务有哪些")
print(f"  -> {r3[:200]}")

print("\n=== Step 4: Assignee completes task ===")
r4 = run_agent(ASSIGNEE, "chat_test", "竞品分析报告 已完成")
print(f"  -> {r4[:150]}")

print("\n=== Step 5: Creator verifies ===")
r5 = run_agent(CREATOR, "chat_test", "验收通过")
print(f"  -> {r5[:150]}")

print("\n=== Final: All tasks ===")
for t in get_all_tasks():
    print(f"  T{t['id']} [{t['status']}] {t['title']} -> {t['assignee_name']}")

print("\n=== End-to-end workflow: COMPLETE ===")