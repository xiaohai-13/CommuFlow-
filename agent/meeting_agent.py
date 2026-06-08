"""MeetingAgent — generates structured meeting minutes"""
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.memory import save_message

PROMPT = """你是 CommuFlow 会议纪要助手。整理会议记录为结构化纪要。
格式：
# 会议纪要
## 主题
## 参会人员
## 讨论要点
## 结论
## 待办事项
| 任务 | 责任人 | 截止时间 |
|------|--------|----------|"""

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)


def run(user_id: str, chat_id: str, message: str, mention_map: dict) -> str:
    result = llm.invoke(PROMPT + f"\n\n会议记录：\n{message}").content
    save_message(chat_id, user_id, "user", message, intent="meeting")
    save_message(chat_id, user_id, "assistant", result, intent="meeting")
    return result
