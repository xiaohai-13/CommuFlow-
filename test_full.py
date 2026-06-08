import sys; sys.path.insert(0, '.')
import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from bot.llm import classify_intent, extract_task_entities, ask_llm

print("=== 1. LLM 连通 ===")
r = ask_llm("回复 OK 即可，不要多余内容")
print(f"结果: {r}")

print("\n=== 2. 意图识别 ===")
tests = [
    ("请@张三 下周五前完成竞品分析报告", "assign_task"),
    ("紧急订单变更流程是什么", "ask_knowledge"),
    ("我的任务有哪些", "query_progress"),
    ("T001 已完成", "complete_task"),
    ("你好", "chat"),
]
ok = 0
for text, expected in tests:
    intent = classify_intent(text)
    match = "OK" if intent["intent"] == expected else f"FAIL(expected={expected})"
    if intent["intent"] == expected: ok += 1
    print(f"  [{match}] {text[:25]:<25} -> {intent['intent']:<16} ({intent['confidence']})")

print(f"\n意图准确率: {ok}/{len(tests)}")

print("\n=== 3. 实体抽取 ===")
e = extract_task_entities("请@李芳 在6月15日前完成市场调研，包含竞品分析")
print(f"  结果: {e}")

print("\n=== 4. 知识问答 ===")
from bot.knowledge import search_knowledge, handle_knowledge
answ = handle_knowledge("紧急订单变更需要哪些部门确认", "u1", "test", "c1", "m1")
print(f"  回答: {answ[:200]}...")

print("\n=== 5. 会议纪要 ===")
from bot.meeting import handle_meeting
min_text = "今天讨论了Q2目标，决定由张三负责市场调研6月20日前完成，李四负责产品优化6月25日前完成"
mins = handle_meeting(min_text, "u1", "test", "c1", "m1")
print(f"  纪要: {mins[:300]}...")

print("\nDONE")
