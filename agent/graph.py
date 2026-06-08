"""LangGraph — orchestrator routes to specialist agents"""
from typing import Literal
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.orchestrator import route
from agent.task_agent import run as task_run
from agent.knowledge_agent import run as knowledge_run
from agent.meeting_agent import run as meeting_run
from utils.logger import logger

FALLBACK = "我是 CommuFlow 助手。可以帮你：\n- 分配任务：@某人 完成XX\n- 查进度：我的任务有哪些\n- 完成任务：T003 已完成\n- 问流程：XX的流程是什么"

graph = None


def route_node(state: AgentState) -> dict:
    """Orchestrator: classify intent, pick agent"""
    last_msg = state["messages"][-1]["content"]
    agent_name = route(last_msg)
    return {"intent": agent_name}


def task_node(state: AgentState) -> dict:
    msg = state["messages"][-1]["content"]
    reply = task_run(state["user_id"], state["chat_id"], msg, state.get("mention_map", {}))
    return {"final_answer": reply}


def knowledge_node(state: AgentState) -> dict:
    msg = state["messages"][-1]["content"]
    reply = knowledge_run(state["user_id"], state["chat_id"], msg, state.get("mention_map", {}))
    return {"final_answer": reply}


def meeting_node(state: AgentState) -> dict:
    msg = state["messages"][-1]["content"]
    reply = meeting_run(state["user_id"], state["chat_id"], msg, state.get("mention_map", {}))
    return {"final_answer": reply}


def chat_node(state: AgentState) -> dict:
    return {"final_answer": FALLBACK}


def router(state: AgentState) -> Literal["task", "knowledge", "meeting", "chat"]:
    return state["intent"]


builder = StateGraph(AgentState)
builder.add_node("route", route_node)
builder.add_node("task", task_node)
builder.add_node("knowledge", knowledge_node)
builder.add_node("meeting", meeting_node)
builder.add_node("chat", chat_node)

builder.set_entry_point("route")
builder.add_conditional_edges("route", router, {
    "task": "task",
    "knowledge": "knowledge",
    "meeting": "meeting",
    "chat": "chat",
})
builder.add_edge("task", END)
builder.add_edge("knowledge", END)
builder.add_edge("meeting", END)
builder.add_edge("chat", END)

graph = builder.compile()


def run_agent(user_id: str, chat_id: str, text: str, mention_map: dict = None) -> str:
    initial = {
        "user_id": user_id,
        "chat_id": chat_id,
        "messages": [{"role": "user", "content": text}],
        "intent": "",
        "extracted_info": {},
        "mention_map": mention_map or {},
        "final_answer": ""
    }
    result = graph.invoke(initial)
    return result["final_answer"]