"""KnowledgeAgent"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.tools import KNOWLEDGE_TOOLS
from agent.memory import save_message, load_history

SYSTEM = """你是 CommuFlow 知识库助手。用 search_sop 检索企业SOP后回答。标注来源。无结果时说"未找到"."""

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)
graph = create_agent(model=llm, tools=KNOWLEDGE_TOOLS, system_prompt=SYSTEM)


def run(user_id: str, chat_id: str, message: str, mention_map: dict) -> str:
    history = load_history(chat_id, user_id, limit=12)
    history_msgs = []
    for h in history:
        role = "assistant" if h["role"] == "assistant" else "user"
        history_msgs.append({"role": role, "content": h["content"]})

    all_msgs = history_msgs + [{"role": "user", "content": message}]
    result = graph.invoke({"messages": all_msgs})
    msgs = result.get("messages", [])
    output = msgs[-1].content if msgs else "处理失败"
    save_message(chat_id, user_id, "user", message, intent="knowledge")
    save_message(chat_id, user_id, "assistant", output, intent="knowledge")
    return output
