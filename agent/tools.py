"""Agent tools — task lifecycle management"""
from langchain.tools import tool
from utils.task_manager import add_task, query_user_tasks, update_task_status, get_task_by_title, get_all_tasks, get_task
from agent.rag import retrieve_context
from utils.logger import logger


@tool
def create_task(title: str, assignee_openid: str, creator_openid: str,
                due_date: str, description: str = "") -> str:
    """创建新任务。返回任务ID。"""
    task_id = add_task(
        title=title, assignee_openid=assignee_openid, assignee_name=assignee_openid,
        creator_openid=creator_openid, creator_name=creator_openid,
        due_date=due_date, description=description
    )
    logger.info(f"task created: T{task_id} {title}")
    return str(task_id)


@tool
def query_my_tasks(user_openid: str) -> str:
    """查询用户的未完成任务列表。"""
    tasks = query_user_tasks(user_openid)
    if not tasks:
        return "你当前没有未完成的任务。"
    lines = []
    for t in tasks:
        status_map = {"pending": "待处理", "in_progress": "进行中", "verified": "待验收"}
        s = status_map.get(t["status"], t["status"])
        tid = str(t["id"]).zfill(3)
        lines.append(f"T{tid} [{s}] {t['title']} 截止:{t.get('due_date','无')}")
    return "\n".join(lines)


@tool
def complete_task(user_openid: str, task_id_or_title: str) -> str:
    """
    标记任务完成（责任人使用）。
    参数: task_id_or_title - 任务ID如T003，或任务标题关键词
    返回任务ID供验收引用。
    """
    task = None
    tid = task_id_or_title.strip().upper()
    if tid.startswith("T") and tid[1:].isdigit():
        task = get_task(int(tid[1:]))
    if not task:
        task = get_task_by_title(task_id_or_title)

    if not task:
        tasks = query_user_tasks(user_openid)
        if tasks:
            task = tasks[0]
        else:
            return "未找到对应任务，请提供任务编号如 T003。"

    update_task_status(task["id"], "verified")
    return f"T{str(task['id']).zfill(3)}"


@tool
def verify_task(user_openid: str, task_id_or_title: str) -> str:
    """
    验收任务（创建者使用）。
    参数: task_id_or_title - 任务ID如T003，或任务标题。留空则自动找最近的待验收任务。
    """
    task = None
    tid = task_id_or_title.strip().upper()
    if tid.startswith("T") and tid[1:].isdigit():
        task = get_task(int(tid[1:]))
    if not task and task_id_or_title:
        task = get_task_by_title(task_id_or_title)
    if not task:
        # Auto-find most recent verified task
        all_tasks = get_all_tasks()
        for t in all_tasks:
            if t["status"] == "verified":
                task = t
                break
    if not task:
        return "没有待验收的任务。请确认任务编号。"
    if task["status"] != "verified":
        return f"T{str(task['id']).zfill(3)}「{task['title']}」当前状态为{task['status']}，请先由责任人标记完成。"

    update_task_status(task["id"], "completed")
    return f"T{str(task['id']).zfill(3)}"


@tool
def search_sop(question: str) -> str:
    """搜索企业SOP知识库。"""
    docs = retrieve_context(question)
    if not docs:
        return "[知识库未找到相关内容]"
    return "\n---\n".join(docs)


ALL_TOOLS = [create_task, query_my_tasks, complete_task, verify_task, search_sop]
TOOL_BY_NAME = {t.name: t for t in ALL_TOOLS}