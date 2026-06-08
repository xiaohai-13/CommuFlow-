from db.models import create_task, get_task, update_task_status, query_user_tasks, get_task_by_id_or_title
from feishu.client import feishu
from bot.llm import extract_task_entities, parse_complete_intent


def handle_assign_task(text: str, sender_openid: str, sender_name: str, chat_id: str, message_id: str) -> str:
    entities = extract_task_entities(text)

    missing = []
    if not entities.get("title"):
        missing.append("标题（任务具体做什么）")
    if not entities.get("assignee"):
        missing.append("责任人（请 @ 负责人）")
    if not entities.get("due_date"):
        missing.append("截止时间（如：本周五 18:00）")

    if missing:
        return f"任务信息不完整，请补充以下内容：\n" + "\n".join(f"• {m}" for m in missing)

    user = feishu.search_user_by_name(entities["assignee"])
    if not user:
        return f"未找到用户「{entities['assignee']}」，请确认姓名或使用飞书邮箱。"
    assignee_openid = user["open_id"]
    assignee_name = user["name"]

    task = create_task(
        title=entities["title"],
        assignee_openid=assignee_openid,
        assignee_name=assignee_name,
        creator_openid=sender_openid,
        creator_name=sender_name,
        due_date=entities.get("due_date", ""),
        description=entities.get("description", ""),
        source_msg=text
    )

    at_assignee = feishu.at_user(assignee_openid)
    return (
        f"✅ 任务「{task['title']}」已创建\n"
        f"ID：{task['id']}\n"
        f"责任人：{at_assignee}\n"
        f"截止时间：{task['due_date']}\n"
        f"状态：{task['status']}\n\n"
        f"完成后请回复「{task['id']} 已完成」"
    )


def handle_complete_task(text: str, sender_openid: str, sender_name: str, chat_id: str, message_id: str) -> str:
    task_id = parse_complete_intent(text)
    if not task_id:
        task = get_task_by_id_or_title(text.replace("已完成", "").replace("做完了", "").strip())
        if task:
            task_id = task["id"]
        else:
            return "未识别任务ID，请提供任务编号（如 T001 已完成）。"

    task = get_task(task_id)
    if not task:
        return f"未找到任务 {task_id}，请确认任务编号。"

    if "验收" in text:
        update_task_status(task_id, "已完成")
        creator_at = feishu.at_user(task["creator_openid"])
        return f"✅ 任务 {task_id} 已验收完成。\n{creator_at} 任务已闭环。"

    update_task_status(task_id, "待验收")
    creator_at = feishu.at_user(task["creator_openid"])
    return (
        f"📋 任务 {task_id}「{task['title']}」已标记为待验收。\n"
        f"{creator_at} 请验收，回复「{task_id} 验收通过」或「{task_id} 需修改」。"
    )


def handle_query_progress(text: str, sender_openid: str, sender_name: str, chat_id: str, message_id: str) -> str:
    tasks = query_user_tasks(sender_openid)
    if not tasks:
        return f"🎉 {sender_name}，你没有未完成的任务。"

    lines = ["📋 你的未完成任务："]
    for t in tasks[:10]:
        status_emoji = {"pending": "⏳", "进行中": "🔄", "待验收": "👀"}.get(t["status"], "❓")
        lines.append(f"{status_emoji} {t['id']} {t['title']} 截止：{t['due_date']} [{t['status']}]")
    return "\n".join(lines)
