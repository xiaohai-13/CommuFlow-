from langchain.tools import tool
from utils.task_manager import add_task
from agent.rag import retrieve_context


@tool
def create_task_tool(title: str, assignee: str, due_date: str, description: str = "") -> str:
    """创建任务。参数：title(任务标题)、assignee(责任人open_id)、due_date(截止时间YYYY-MM-DD)、description(详情)"""
    task_id = add_task(
        title=title, assignee_openid=assignee, assignee_name=assignee,
        creator_openid="system", creator_name="CommuFlow",
        due_date=due_date, description=description
    )
    return f"T{task_id:03d} {title} {assignee} {due_date}"


@tool
def search_knowledge(query: str) -> str:
    """从内部知识库检索相关信息。参数：query(查询问题)"""
    docs = retrieve_context(query)
    if not docs:
        return "未找到相关知识"
    return "\n---\n".join(docs)


@tool
def generate_meeting_minutes(transcript: str) -> str:
    """根据会议转录文本生成结构化纪要。参数：transcript(会议记录全文)"""
    return transcript


tools = [create_task_tool, search_knowledge, generate_meeting_minutes]