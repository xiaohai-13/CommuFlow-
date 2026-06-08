from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import intent_node, extract_node, tool_node


builder = StateGraph(AgentState)
builder.add_node("intent", intent_node)
builder.add_node("extract", extract_node)
builder.add_node("tool_call", tool_node)

builder.set_entry_point("intent")
builder.add_edge("intent", "extract")
builder.add_edge("extract", "tool_call")
builder.add_edge("tool_call", END)

graph = builder.compile()


def run_agent(user_id: str, chat_id: str, text: str) -> str:
    initial_state = {
        "user_id": user_id,
        "chat_id": chat_id,
        "messages": [{"role": "user", "content": text}],
        "intent": "",
        "extracted_info": {},
        "final_answer": ""
    }
    final_state = graph.invoke(initial_state)
    return final_state["final_answer"]