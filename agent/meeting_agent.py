"""MeetingAgent"""
from agent.base import create_agent
from agent.tools import MEETING_TOOLS
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

PROMPT = """你是 CommuFlow 会议纪要助手。将会议记录整理成结构化纪要。

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
    from agent.memory import save_message
    result = llm.invoke(PROMPT + f"\n\n会议记录：\n{message}").content
    save_message(user_id, "user", message, intent="meeting")
    save_message(user_id, "assistant", result, intent="meeting")
    return result