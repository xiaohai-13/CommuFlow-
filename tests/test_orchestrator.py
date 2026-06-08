"""L1: Orchestrator routing test — requires LLM"""
import sys, io
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.orchestrator import route

tests = [
    ("请@张三 周五前完成报告", "task"),
    ("紧急订单变更流程是什么", "knowledge"),
    ("帮我整理会议记录：今天讨论了Q2目标...", "meeting"),
    ("我的任务有哪些", "task"),
    ("T001 已完成", "task"),
    ("验收通过", "task"),
    ("你好", "chat"),
    ("今天天气怎么样", "chat"),
]

print("=== L1: Orchestrator routing ===")
ok = 0
for msg, expected in tests:
    result = route(msg)
    status = "OK" if result == expected else f"FAIL (expected {expected})"
    if result == expected:
        ok += 1
    print(f"  [{status}] {msg[:30]:<30} -> {result}")

print(f"\n  {ok}/{len(tests)} passed")