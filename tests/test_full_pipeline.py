"""
CommuFlow full pipeline acceptance test.

This script is intentionally verbose. It prints:
- who sent the Feishu-like message,
- what the original message looked like,
- what the expected behavior is,
- what CommuFlow replied,
- and the task-board state after important steps.

Usage:
    python tests/test_full_pipeline.py
"""
import io
import json
import re
import sqlite3
import sys

sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from agent.graph import run_agent
from agent.memory import clear_history
from agent.tools import create_task
from utils.task_manager import DB_PATH, add_role, get_all_tasks, get_task, init_db


CHAT = "oc_test_full_pipeline"
BOT_NAME = "CommuFlow"
BOT_OPENID = "ou_commuflow_bot"
USERS = {
    "小海": "ou_xiaohai",
    "张三": "ou_zhangsan",
    "李四": "ou_lisi",
    "王五": "ou_wangwu",
    "路人": "ou_other",
}


def reset_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    for table in ("tasks", "roles", "task_events"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
    clear_history(CHAT)
    add_role(USERS["小海"], "creator")


def make_mentions(*names):
    """Build a Feishu-like mentions map.

    In a real Feishu group message, the first mention is usually the bot:
    @_user_1 -> CommuFlow
    @_user_2 -> assignee
    """
    mapping = {"@_user_1": {"name": BOT_NAME, "open_id": BOT_OPENID}}
    for index, name in enumerate(names, 2):
        mapping[f"@_user_{index}"] = {"name": name, "open_id": USERS[name]}
    return mapping


def normalize_message(text, mentions):
    normalized = text
    for key, info in mentions.items():
        normalized = normalized.replace(key, f"@{info['name']}")
    return normalized


def send(actor, raw_text, expected, mentions=None):
    mentions = mentions or {}
    normalized = normalize_message(raw_text, mentions)
    print("\n" + "." * 70)
    print(f"发言人: {actor} ({USERS[actor]})")
    print(f"飞书原文: {raw_text}")
    if mentions:
        print("mentions:")
        for key, info in mentions.items():
            print(f"  {key} -> {info['name']} ({info['open_id']})")
    print(f"归一化后: {normalized}")
    print(f"预期行为: {expected}")
    reply = run_agent(USERS[actor], CHAT, normalized, mentions)
    print("CommuFlow 回复:")
    print(reply)
    return reply


def must_contain(text, expected, label):
    assert expected in text, f"{label}: expected {expected!r} in reply:\n{text}"


def must_not_contain(text, unexpected, label):
    assert unexpected not in text, f"{label}: unexpected {unexpected!r} in reply:\n{text}"


def extract_task_id(reply):
    match = re.search(r"T\d{3}", reply)
    assert match, f"expected task id in reply:\n{reply}"
    return match.group()


def board(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    rows = get_all_tasks()
    if not rows:
        print("(empty)")
        return
    print(f"{'ID':<6} {'Status':<12} {'Title':<22} {'Assignee':<14} {'Creator':<14} {'Due Date'}")
    print("-" * 90)
    for task in rows:
        print(
            f"T{task['id']:03d}  {task['status']:<12} "
            f"{task['title']:<22} {task['assignee_openid'][:14]:<14} "
            f"{task['creator_openid'][:14]:<14} {task['due_date']}"
        )


def create_fixture(title, assignee, creator, due_date):
    result = json.loads(create_task.invoke({
        "title": title,
        "assignee_openid": USERS[assignee],
        "creator_openid": USERS[creator],
        "due_date": due_date,
    }))
    print(f"系统夹具: 创建 T{result['id']} {title} -> {assignee}, creator={creator}")
    return f"T{result['id']}"


reset_db()

print("=" * 70)
print("CommuFlow Full Pipeline Acceptance Test")
print("=" * 70)
print("初始角色:")
print("- 小海: creator role, can create and verify tasks")
print("- 张三/李四/王五: normal Feishu users, can only operate assigned tasks")
print("- 路人: no task permissions")
board("初始任务看板")


print("\n\n### 场景 1: 权限入口检查 - 非创建者不能派任务")
reply = send(
    "路人",
    "@_user_1 请@_user_2 2026-06-19前完成竞品分析报告",
    "应拒绝创建，因为路人不是 creator/admin",
    make_mentions("张三"),
)
must_contain(reply, "只有管理员或任务创建白名单成员可以创建任务", "non-creator create denied")
board("场景 1 后任务看板，应仍为空")


print("\n\n### 场景 2: 标准闭环 - 创建、查询、详情、完成、验收")
reply = send(
    "小海",
    "@_user_1 请@_user_2 2026-06-19前完成竞品分析报告",
    "应创建任务给张三，并返回任务 ID",
    make_mentions("张三"),
)
task_report = extract_task_id(reply)
must_contain(reply, "已创建", "create task")
assert get_task(int(task_report[1:]))["assignee_openid"] == USERS["张三"], "task must be assigned to 张三, not bot"
board("创建任务后")

reply = send("张三", "我的任务有哪些", "张三应只看到分配给自己的任务")
must_contain(reply, task_report, "assignee query")

reply = send("张三", f"{task_report} 任务是什么", "责任人可查看任务详情")
must_contain(reply, "状态:", "detail by assignee")
must_contain(reply, "竞品分析报告", "detail title")

reply = send("张三", f"{task_report} 已完成", "责任人可标记完成，任务进入待验收")
must_contain(reply, "待验收", "complete task")
board("张三完成任务后")

reply = send("小海", f"{task_report} 验收通过", "创建者可验收任务，任务闭环完成")
must_contain(reply, "闭环完成", "verify task")
board("小海验收后")


print("\n\n### 场景 3: 多人任务隔离和越权拦截")
mentions = make_mentions("张三", "李四")
reply = send(
    "小海",
    "@_user_1 请@_user_2 2026-06-20前完成后端API开发",
    "应创建张三的后端任务",
    mentions,
)
task_api = extract_task_id(reply)
assert get_task(int(task_api[1:]))["assignee_openid"] == USERS["张三"], "backend task must be assigned to 张三"

reply = send(
    "小海",
    "@_user_1 请@_user_3 2026-06-18前完成UI设计稿",
    "应创建李四的 UI 任务",
    mentions,
)
task_ui = extract_task_id(reply)
assert get_task(int(task_ui[1:]))["assignee_openid"] == USERS["李四"], "UI task must be assigned to 李四"
board("多人任务创建后")

reply = send("张三", "我的任务有哪些", "张三只能看到自己的后端任务")
must_contain(reply, task_api, "zhangsan sees own task")
must_not_contain(reply, task_ui, "zhangsan cannot see lisi task")

reply = send("李四", "我的任务有哪些", "李四只能看到自己的 UI 任务")
must_contain(reply, task_ui, "lisi sees own task")
must_not_contain(reply, task_api, "lisi cannot see zhangsan task")

reply = send("路人", f"{task_api} 已完成", "路人不是责任人，应无法完成张三任务")
must_contain(reply, "只有任务责任人可以标记完成", "unauthorized complete")

reply = send("路人", f"{task_api} 验收通过", "路人不是创建者，应无法验收")
must_contain(reply, "只有任务创建者或管理员", "unauthorized verify")

reply = send("路人", f"{task_api} 任务是什么", "路人不是相关人，应无法查看详情")
must_contain(reply, "没有权限", "unauthorized detail")


print("\n\n### 场景 4: 任务详情消歧 - 同名/相似任务必须让用户选 ID")
fixture_1 = create_fixture("竞品分析报告-二期", "张三", "小海", "2026-06-21")
fixture_2 = create_fixture("竞品分析报告-三期", "张三", "小海", "2026-06-22")
board("制造两个相似任务后")

reply = send(
    "小海",
    "竞品分析报告 任务是什么",
    "应进入 TaskAgent，并返回多个候选任务，不应走知识库",
)
must_contain(reply, "匹配到多个任务", "ambiguous detail")
must_contain(reply, fixture_1, "ambiguous candidate 1")
must_contain(reply, fixture_2, "ambiguous candidate 2")


print("\n\n### 场景 5: 知识问答 - SOP/RAG")
reply = send("小海", "紧急订单变更流程是什么？", "应进入 KnowledgeAgent，检索 SOP 并回答")
assert "未找到" not in reply, f"knowledge query should find SOP:\n{reply}"
must_contain(reply, "订单", "knowledge answer")


print("\n\n### 场景 6: 会议纪要")
meeting = (
    "帮我整理会议纪要：今天下午开了Q2产品评审会。参会人员：小海、张三、李四。"
    "讨论了竞品报告、后端API和UI设计。结论：张三6月20日前补充竞品数据，"
    "李四6月18日前完成UI设计稿。"
)
reply = send("小海", meeting, "应进入 MeetingAgent，生成结构化会议纪要")
must_contain(reply, "会议纪要", "meeting minutes")
must_contain(reply, "待办", "meeting action items")


print("\n\n### 场景 7: 闲聊兜底")
reply = send("小海", "你好", "应进入 Chat fallback，返回能力说明")
must_contain(reply, "CommuFlow", "chat fallback")

board("最终任务看板")
print("\nFULL PIPELINE ACCEPTANCE TESTS PASSED")
