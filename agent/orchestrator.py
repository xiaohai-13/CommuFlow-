"""Orchestrator routes to specialist agents and does not execute business logic."""
import re

from langchain_openai import ChatOpenAI

from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from utils.logger import logger


llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=0,
)


ROUTE_PROMPT = """Classify the user message. Output only one agent name:
task / knowledge / meeting / chat

task:
- assign work, create task, follow up, my tasks, task status, task detail
- completed/done/verify/reject/update/cancel/reassign/remind
- messages that mention task ids like T001

knowledge:
- SOP, process, policy, standard, FAQ, how to operate
- general enterprise knowledge questions not tied to a concrete task

meeting:
- meeting notes, minutes, transcript, action item extraction

chat:
- greeting or unrelated chat

Message: {message}
Agent:"""


TASK_PATTERNS = [
    r"T\d{3}",
    r"我的任务",
    r"任务有哪些",
    r"任务是什么",
    r"任务状态",
    r"现在怎么样",
    r"谁负责",
    r"负责人",
    r"已完成",
    r"完成了",
    r"做完了",
    r"搞定了",
    r"验收",
    r"驳回",
    r"需修改",
    r"需要修改",
    r"截止时间",
    r"转给",
    r"取消任务",
    r"请@",
    r"请 @",
]

MEETING_PATTERNS = [
    r"会议纪要",
    r"会议记录",
    r"转录",
    r"整理会议",
    r"生成纪要",
]


def _rule_route(message: str) -> str | None:
    for pattern in MEETING_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return "meeting"
    for pattern in TASK_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return "task"
    return None


def route(message: str) -> str:
    """Classify intent and return agent name."""
    rule_agent = _rule_route(message)
    if rule_agent:
        logger.info(f"route: {rule_agent} <- {message[:50]} (rule)")
        return rule_agent

    prompt = ROUTE_PROMPT.format(message=message)
    result = llm.invoke(prompt).content.strip().lower()
    agent = result.split()[0] if result else "chat"
    if agent not in ("task", "knowledge", "meeting", "chat"):
        agent = "chat"
    logger.info(f"route: {agent} <- {message[:50]} (llm)")
    return agent
