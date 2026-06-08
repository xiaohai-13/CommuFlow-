"""Orchestrator — routes to specialist agent, does NOT execute business logic"""
import json, re
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from utils.logger import logger

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)

ROUTE_PROMPT = """判断用户意图，只输出agent名称（task/knowledge/meeting/chat）：

- task: 分配任务、安排工作、@某人、完成/负责/跟进、进度查询、我的任务、已完成、做完了、验收
- knowledge: 流程、规定、SOP、怎么做、是什么、怎么操作、制度、规范
- meeting: 会议记录、纪要、转录、帮我整理会议
- chat: 闲聊、问候、无法归类

消息：{message}
Agent："""


def route(message: str) -> str:
    """Classify intent → return agent name"""
    # T00X pattern always goes to task agent
    if re.search(r"T\d{3}", message):
        return "task"

    prompt = ROUTE_PROMPT.format(message=message)
    result = llm.invoke(prompt).content.strip().lower()
    agent = result.split()[0] if result else "chat"
    if agent not in ("task", "knowledge", "meeting", "chat"):
        agent = "chat"
    logger.info(f"route: {agent} <- {message[:50]}")
    return agent