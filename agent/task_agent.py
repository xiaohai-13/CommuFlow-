"""TaskAgent — create_agent with task tools"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.tools import TASK_TOOLS
from agent.memory import save_message

SYSTEM = """你是 CommuFlow 任务管理助手。处理用户的任务请求。

规则：
1. 分配任务：提取标题、责任人、截止时间。缺信息反问。
2. 用 create_task 创建，回复含 T00X ID。
3. 含 T00X 的消息 → 查任务状态：pending 用 complete_task, verified 用 verify_task。
4. 查进度用 query_my_tasks。
5. 回复包含任务ID，简洁引导下一步。"""

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)
graph = create_agent(model=llm, tools=TASK_TOOLS, system_prompt=SYSTEM)


def run(user_id: str, chat_id: str, message: str, mention_map: dict) -> str:
    result = graph.invoke({"messages": [{"role": "user", "content": message}]})
    msgs = result.get("messages", [])
    output = msgs[-1].content if msgs else "处理失败"
    save_message(chat_id, "user", message, intent="task")
    save_message(chat_id, "assistant", output, intent="task")
    return output