"""Agent tools — proper LangChain tool definitions"""
from langchain.tools import tool
from utils.task_manager import add_task, query_user_tasks, update_task_status, get_task_by_title, get_all_tasks
from agent.rag import retrieve_context
from utils.logger import logger


@tool
def create_task(title: str, assignee_openid: str, due_date: str, description: str = "") -> str:
    """创建新任务。当用户要求分配任务、安排工作、指定责任人时使用。"""
    task_id = add_task(
        title=title, assignee_openid=assignee_openid, assignee_name=assignee_openid,
        creator_openid="system", creator_name="CommuFlow",
        due_date=due_date, description=description
    )
    logger.info(f"task created: T{task_id} {title}")
    return f"T{task_id} {title} {due_date}"


@tool
def query_my_tasks(user_openid: str) -> str:
    """查询用户的未完成任务列表。当用户询问我的任务、未完成的、进度时使用。"""
    tasks = query_user_tasks(user_openid)
    if not tasks:
        return "你当前没有未完成的任务。"
    lines = []
    for t in tasks:
        status_map = {"pending": "待处理", "in_progress": "进行中", "verified": "待验收"}
        s = status_map.get(t["status"], t["status"])
        lines.append(f"T{str(t['id']).zfill(3)} [{s}] {t['title']} 截止:{t.get('due_date','无')}")
    return "\n".join(lines)


@tool
def mark_task_complete(user_openid: str, task_keyword: str) -> str:
    """标记任务为完成或验收。当用户说已完成、做完了、验收通过时使用。"""
    is_verify = "验收" in task_keyword

    task = get_task_by_title(task_keyword)
    if not task:
        tasks = query_user_tasks(user_openid)
        if tasks:
            task = tasks[0]
        elif is_verify:
            all_tasks = get_all_tasks()
            for t in all_tasks:
                if t["status"] == "verified":
                    task = t
                    break
        if not task:
            return "未找到对应任务，请提供任务标题。"

    if is_verify:
        update_task_status(task["id"], "completed")
        return f"T{str(task['id']).zfill(3)} {task['title']} 验收通过，已闭环。"
    else:
        update_task_status(task["id"], "verified")
        return f"T{str(task['id']).zfill(3)} {task['title']} 已标记待验收。请创建者回复验收通过。"


@tool
def search_sop(question: str) -> str:
    """搜索企业SOP知识库。当用户询问流程、规定、制度、怎么操作时使用。"""
    docs = retrieve_context(question)
    if not docs:
        return "[知识库未找到相关内容]"
    return "\n---\n".join(docs)


ALL_TOOLS = [create_task, query_my_tasks, mark_task_complete, search_sop]
TOOL_BY_NAME = {t.name: t for t in ALL_TOOLS}