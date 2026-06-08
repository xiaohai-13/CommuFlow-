from bot.llm import classify_intent
from bot.task import handle_assign_task, handle_complete_task, handle_query_progress
from bot.knowledge import handle_knowledge
from bot.meeting import handle_meeting

CONFIDENCE_THRESHOLD = 0.6


def route_message(text: str, sender_openid: str, sender_name: str, chat_id: str, message_id: str) -> str:
    intent = classify_intent(text)
    intent_type = intent.get("intent", "chat")
    confidence = intent.get("confidence", 0)

    if confidence < CONFIDENCE_THRESHOLD and intent_type != "chat":
        return _fallback_help()

    handlers = {
        "assign_task": handle_assign_task,
        "complete_task": handle_complete_task,
        "query_progress": handle_query_progress,
        "ask_knowledge": handle_knowledge,
        "meeting_minutes": handle_meeting,
    }

    handler = handlers.get(intent_type)
    if handler:
        return handler(text, sender_openid, sender_name, chat_id, message_id)

    return "你好！我是 CommuFlow 助手。你可以：\n• 分配任务：请 @某人 完成XX，截止周五\n• 查进度：我的未完成的任务有哪些\n• 问流程：XX的流程是什么\n• 生成纪要：发送会议记录，我帮你整理"


def _fallback_help() -> str:
    return (
        "我没理解您的意思，试试这样说：\n"
        "• 🎯 分配任务：「请 @张三 周五前完成竞品分析报告」\n"
        "• 📚 问流程：「紧急订单变更流程是什么？」\n"
        "• 📊 查进度：「我的任务有哪些？」\n"
        "• ✅ 完成任务：「T001 已完成」"
    )
