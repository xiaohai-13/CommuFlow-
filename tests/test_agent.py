"""Simple local test — agent logic without Feishu"""
import sys, io
sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent

print("=== 1. Intent: assign_task ===")
r = run_agent("u1", "c1", "请@张三 下周五前完成竞品分析报告，包含市场规模对比")
print(f"Result: {r[:150]}")

print("\n=== 2. Intent: knowledge ===")
r = run_agent("u1", "c1", "紧急订单变更流程是什么？需要哪些部门确认？")
print(f"Result: {r[:200]}")

print("\n=== 3. Intent: query ===")
r = run_agent("u1", "c1", "我的任务有哪些")
print(f"Result: {r[:100]}")

print("\n=== 4. Intent: chat ===")
r = run_agent("u1", "c1", "你好")
print(f"Result: {r[:100]}")

print("\n=== All tests done ===")