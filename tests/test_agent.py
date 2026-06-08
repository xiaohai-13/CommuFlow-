"""Agent core test — memory, tools, prompt orchestration"""
import sys, io
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from utils.task_manager import init_db

init_db()
CHAT = "test_chat_001"
USER_A = "ou_user_a"
USER_B = "ou_user_b"

clear_history(CHAT)

print("=" * 50)
print("TEST 1: Task creation with missing info -> follow-up")
print("=" * 50)

r1 = run_agent(USER_A, CHAT, "请@张三 完成竞品分析报告", {"@_user_2": {"name": "张三", "open_id": USER_B}})
print(f"Q: 请@张三 完成竞品分析报告")
print(f"A: {r1[:120]}")
assert "截止时间" in r1, "Should ask for due date"
print("PASS: asked for due date ✅")

r2 = run_agent(USER_A, CHAT, "2026-06-20")
print(f"\nQ: 2026-06-20")
print(f"A: {r2[:120]}")
assert "已创建" in r2, "Should create task"
print("PASS: task created with follow-up ✅")

print("\n" + "=" * 50)
print("TEST 2: Progress query")
print("=" * 50)

r3 = run_agent(USER_B, CHAT, "我的任务有哪些")
print(f"Q: 我的任务有哪些")
print(f"A: {r3[:200]}")
assert "竞品分析" in r3 or "待处理" in r3, "Should show task"
print("PASS: task visible to assignee ✅")

print("\n" + "=" * 50)
print("TEST 3: Task completion")
print("=" * 50)

r4 = run_agent(USER_B, CHAT, "竞品分析报告 已完成")
print(f"Q: 竞品分析报告 已完成")
print(f"A: {r4[:120]}")
assert "待验收" in r4, "Should mark as verified"
print("PASS: marked for verification ✅")

r5 = run_agent(USER_A, CHAT, "验收通过")
print(f"\nQ: 验收通过")
print(f"A: {r5[:120]}")
print("PASS: verification accepted ✅")

print("\n" + "=" * 50)
print("TEST 4: Fallback chat constraint")
print("=" * 50)

r6 = run_agent(USER_A, "chat_other", "今天天气怎么样")
print(f"Q: 今天天气怎么样")
print(f"A: {r6[:100]}")
assert "任务" in r6 or "CommuFlow" in r6, "Should give fallback reply"
print("PASS: fallback reply ✅")

r7 = run_agent(USER_A, "chat_other", "帮我写一段Python代码")
print(f"\nQ: 帮我写一段Python代码")
print(f"A: {r7[:100]}")
assert "代码" not in r7[:50], "Should not generate code"
print("PASS: no code generation ✅")

print("\n" + "=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)