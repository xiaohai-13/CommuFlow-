"""TaskAgent — Pydantic validated + JSON prompt (brace-safe)"""
import json, re
from datetime import datetime, date, timedelta
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.schemas import TaskAction, ActionPlan
from agent.tools import create_task, complete_task, verify_task, query_my_tasks
from agent.memory import save_message

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)

# NOTE: braces are literal JSON, NOT format placeholders. Use .replace() not .format()!
EXTRACT_PROMPT = """你是任务助手。分析消息，输出JSON:
{"steps":[{"action":"create|complete|verify|query|clarify|chat","task_title":"","task_id":"","assignee_name":"","due_date":""}]}

规则:
- "请@某人 XX前完成YY" -> action=create, task_title=YY, assignee_name=某人, due_date=XX(日期)
- "XXX已完成"/"T00X已完成" -> action=complete, task_title/task_id=任务名或编号
- "验收通过"/"T00X验收通过" -> action=verify, task_id=编号或""
- "我的任务"/"进度查询" -> action=query
- 闲聊 -> action=chat
- 信息不全 -> action=clarify

日期映射: 下周五=NEXT_FRIDAY, 下周一=NEXT_MONDAY, 今天=TODAY

消息: MESSAGE

只输出JSON:"""

FALLBACK = """我是 CommuFlow 任务助手。可帮你：
- 分配：@某人 完成XX
- 查进度：我的任务有哪些
- 完成：T003 已完成
- 验收：T003 验收通过"""


def _compute_dates():
    today = date.today()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    next_friday = today + timedelta(days=days_until_friday)
    days_until_monday = (0 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    return today.isoformat(), next_friday.isoformat(), next_monday.isoformat()


def _resolve_assignee(name: str, mention_map: dict) -> str:
    if not name or not mention_map:
        return ""
    for info in mention_map.values():
        if info["name"] == name:
            return info["open_id"]
    return ""


def _parse_plan(raw: str) -> ActionPlan:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    m = re.search(r'\{[\s\S]*\}', raw)
    if not m:
        raise ValueError("No JSON found")
    data = json.loads(m.group())
    return ActionPlan(**data)


def _execute_step(step: TaskAction, user_id: str, mention_map: dict) -> str:
    action = step.action
    task_ref = step.task_id or step.task_title
    assignee_name = step.assignee_name
    due_date = step.due_date
    assignee_openid = _resolve_assignee(assignee_name, mention_map)

    if action == "create":
        if not task_ref:
            return "请明确任务标题。"
        if not assignee_openid:
            return f"请 @ 责任人，例如：请@张三 {task_ref}。"
        if not due_date:
            return f"请明确截止时间，例如：下周五18:00 或 2026-06-15。"
        r = create_task.invoke({
            "title": task_ref, "assignee_openid": assignee_openid,
            "creator_openid": user_id, "due_date": due_date,
        })
        data = json.loads(r) if isinstance(r, str) else r
        return (
            f"[OK] 任务「{task_ref}」已创建\n"
            f"  ID: T{data['id']}  责任人: {assignee_name}  截止: {due_date}\n"
            f"  完成后回复「T{data['id']} 已完成」"
        )

    elif action == "complete":
        r = complete_task.invoke({"user_openid": user_id, "task_id_or_title": task_ref})
        if "NOT_FOUND" in str(r):
            return f"[FAIL] 未找到任务「{task_ref}」，请提供标题或编号。"
        data = json.loads(r) if isinstance(r, str) else r
        return f"[OK] T{data['id']} {data['title']} 已标记待验收。创建者回复「T{data['id']} 验收通过」确认。"

    elif action == "verify":
        r = verify_task.invoke({"user_openid": user_id, "task_id_or_title": task_ref})
        if "NOT_FOUND" in str(r):
            return "[FAIL] 未找到待验收任务。"
        if "NOT_VERIFIED" in str(r):
            return "[FAIL] 该任务尚未标记完成。先让责任人回复完成任务。"
        data = json.loads(r) if isinstance(r, str) else r
        return f"[OK] T{data['id']} {data['title']} 验收通过！闭环完成。"

    elif action == "query":
        r = query_my_tasks.invoke({"user_openid": user_id})
        tasks = json.loads(r) if isinstance(r, str) else []
        if not tasks:
            return "你当前没有未完成的任务。"
        lines = ["你的任务："]
        for t in tasks:
            st = {"pending": "待处理", "verified": "待验收"}.get(t["status"], t["status"])
            lines.append(f"  T{t['id']} [{st}] {t['title']} 截止:{t['due_date']}")
        return "\n".join(lines)

    elif action == "clarify":
        return "请补充完整信息。例如：请@张三 下周五18:00前完成竞品分析报告。"

    else:
        return FALLBACK


def run(user_id: str, chat_id: str, message: str, mention_map: dict) -> str:
    today, next_friday, next_monday = _compute_dates()

    save_message(chat_id, user_id, "user", message, intent="task")

    # Build prompt safely (no .format() to avoid brace conflicts)
    prompt = EXTRACT_PROMPT.replace("TODAY", today)
    prompt = prompt.replace("NEXT_FRIDAY", next_friday)
    prompt = prompt.replace("NEXT_MONDAY", next_monday)
    prompt = prompt.replace("MESSAGE", message)

    try:
        raw = llm.invoke(prompt).content
        plan = _parse_plan(raw)
    except Exception:
        save_message(chat_id, user_id, "assistant", FALLBACK, intent="task")
        return FALLBACK

    replies = [_execute_step(s, user_id, mention_map) for s in plan.steps]
    result = "\n\n".join(replies) if replies else FALLBACK
    save_message(chat_id, user_id, "assistant", result, intent="task")
    return result
