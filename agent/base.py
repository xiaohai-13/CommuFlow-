"""Base agent — shared logic for all specialist agents"""
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.memory import save_message


def create_agent(system_prompt: str, tools: list) -> AgentExecutor:
    """Create a LangChain agent with given prompt and tools"""
    llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)
    agent = create_tool_calling_agent(llm, tools, system_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)


def run_agent(executor: AgentExecutor, user_id: str, chat_id: str,
              message: str, intent: str) -> str:
    """Run agent and save to memory"""
    result = executor.invoke({"input": message, "user_id": user_id})
    output = result["output"]
    save_message(chat_id, "user", message, intent=intent)
    save_message(chat_id, "assistant", output, intent=intent)
    return output