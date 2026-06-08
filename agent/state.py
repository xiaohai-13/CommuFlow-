from typing import List, Dict, Any, TypedDict, Annotated
import operator


class AgentState(TypedDict):
    user_id: str
    chat_id: str
    messages: Annotated[List[Dict[str, str]], operator.add]
    intent: str
    extracted_info: Dict[str, Any]
    tool_calls: List[Dict]
    final_answer: str