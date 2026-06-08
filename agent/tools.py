"""Tools — grouped by specialist agent"""
from langchain.tools import tool
from utils.task_manager import add_task, query_user_tasks, update_task_status, get_task_by_title, get_all_tasks, get_task
from agent.rag import retrieve_context
from utils.logger import logger


# ═══════════ TASK AGENT TOOLS ═══════════

@tool
def create_task(title: str, assignee_openid: str, creator_openid: str, due_date: str) -> str:
    """Create a new task. Use when user wants to assign work to someone."""
    task_id = add_task(
        title=title, assignee_openid=assignee_openid, assignee_name="",
        creator_openid=creator_openid, creator_name="",
        due_date=due_date, description=""
    )
    logger.info(f"task created: {task_id} {title}")
    return str(task_id)


@tool
def complete_task(user_openid: str, task_id_or_title: str) -> str:
    """Mark a task as done (assignee marks their own task complete)."""
    task = _find_task(task_id_or_title, user_openid)
    if not task:
        return "NOT_FOUND"
    update_task_status(task["id"], "verified")
    return str(task["id"])


@tool
def verify_task(user_openid: str, task_id_or_title: str) -> str:
    """Verify/accept a completed task (creator confirms). If no ID, auto-find pending verification."""
    task = _find_task(task_id_or_title, user_openid)
    if not task:
        # Auto-find verified task
        for t in get_all_tasks():
            if t["status"] == "verified":
                task = t
                break
    if not task:
        return "NOT_FOUND"
    if task["status"] != "verified":
        return "NOT_VERIFIED"
    update_task_status(task["id"], "completed")
    return str(task["id"])


@tool
def query_my_tasks(user_openid: str) -> str:
    """Get a list of user's unfinished tasks."""
    tasks = query_user_tasks(user_openid)
    if not tasks:
        return "[]"
    import json
    result = []
    for t in tasks:
        result.append({
            "id": str(t["id"]).zfill(3),
            "title": t["title"],
            "status": t["status"],
            "due_date": t.get("due_date", "")
        })
    return json.dumps(result, ensure_ascii=False)


def _find_task(keyword: str, user_openid: str = "") -> dict | None:
    """Find task by T00X ID, title keyword, or user's latest"""
    tid = keyword.strip().upper()
    if tid.startswith("T") and tid[1:].isdigit():
        return get_task(int(tid[1:]))
    if keyword:
        return get_task_by_title(keyword)
    if user_openid:
        tasks = query_user_tasks(user_openid)
        if tasks:
            return tasks[0]
    return None


TASK_TOOLS = [create_task, complete_task, verify_task, query_my_tasks]


# ═══════════ KNOWLEDGE AGENT TOOLS ═══════════

@tool
def search_sop(question: str) -> str:
    """Search enterprise SOP/knowledge base for relevant information."""
    docs = retrieve_context(question)
    if not docs:
        return "NO_RESULTS"
    return "\n---\n".join(docs)


KNOWLEDGE_TOOLS = [search_sop]


# ═══════════ MEETING AGENT TOOLS ═══════════

MEETING_TOOLS = []