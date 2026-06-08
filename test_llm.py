import sys; sys.path.insert(0, '.')
from bot.llm import classify_intent, extract_task_entities, ask_llm

print("=== 1. LLM ===", flush=True)
try:
    r = ask_llm("回复OK")
    print("OK:", r, flush=True)
except Exception as e:
    print("ERR:", e, flush=True)

print("=== 2. 意图 ===", flush=True)
for t in ["请@张三 周五前完成报告", "流程是什么", "你好"]:
    intent = classify_intent(t)
    print(f"  {intent}", flush=True)

print("=== 3. 实体 ===", flush=True)
e = extract_task_entities("请@李芳 6月15日前完成市场调研")
print(f"  {e}", flush=True)

print("DONE", flush=True)
