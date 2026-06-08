"""KnowledgeAgent"""
from agent.base import create_agent
from agent.tools import KNOWLEDGE_TOOLS

PROMPT = """你是 CommuFlow 知识库助手。根据企业SOP回答流程问题。

规则：
1. 用 search_sop 检索知识库
2. 基于检索结果回答，标注来源
3. 无结果时说"未找到相关知识"
4. 简洁专业，不编造

当前用户ID: {user_id}"""

executor = create_agent(PROMPT, KNOWLEDGE_TOOLS)


def run(user_id: str, chat_id: str, message: str, mention_map: dict) -> str:
    from agent.base import run_agent
    return run_agent(executor, user_id, chat_id, message, "knowledge")