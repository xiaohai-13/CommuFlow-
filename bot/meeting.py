from bot.llm import generate_meeting_minutes, extract_todos_from_minutes
from bot.task import handle_assign_task


def handle_meeting(text: str, sender_openid: str, sender_name: str, chat_id: str, message_id: str) -> str:
    minutes = generate_meeting_minutes(text)
    todos = extract_todos_from_minutes(minutes)
    parts = [minutes]

    if todos:
        created = []
        for todo in todos:
            created.append(f"• {todo.get('task','')} @{todo.get('assignee','')} 截止：{todo.get('due','')}")
        parts.append(f"\n📋 已识别 {len(todos)} 个待办事项：\n" + "\n".join(created))

    return "\n".join(parts)
