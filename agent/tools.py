"""Tools — grouped by specialist agent"""
from langchain.tools import tool
from utils.task_manager import (
    add_task, query_user_tasks, update_task_status, get_task_by_title,
    get_all_tasks, get_task, add_task_event
)
from utils.auth import authorize, is_admin
from agent.rag import retrieve_context
from utils.logger import logger
import json


# ═══════════ TASK AGENT TOOLS ═══════════
@tool
def create_task(title: str, assignee_openid: str, creator_openid: str, due_date: str) -> str:
    """Create a new task. Use when user wants to assign work to someone."""
    auth = authorize(creator_openid, "create_task")
    if not auth.allowed:
        return json.dumps({"error": "UNAUTHORIZED", "reason": auth.reason}, ensure_ascii=False)
    task_id = add_task(
        title=title, assignee_openid=assignee_openid, assignee_name="",
        creator_openid=creator_openid, creator_name="",
        due_date=due_date, description=""
    )
    add_task_event(task_id, creator_openid, "create_task", "", "pending", json.dumps({
        "title": title,
        "assignee_openid": assignee_openid,
        "due_date": due_date,
    }, ensure_ascii=False))
    logger.info(f"task created: {task_id} {title}")
    return json.dumps({"id": str(task_id).zfill(3), "title": title, "status": "pending"}, ensure_ascii=False)


@tool
def get_task_status(task_id_or_title: str) -> str:
    """Look up a task's current status. Returns JSON with id, title, status, assignee, creator, due_date."""
    import json
    task = _find_task(task_id_or_title)
    if not task:
        return "NOT_FOUND"
    return json.dumps({
        "id": str(task["id"]).zfill(3),
        "title": task["title"],
        "status": task["status"],
        "assignee": task.get("assignee_openid", ""),
        "creator": task.get("creator_openid", ""),
        "due_date": task.get("due_date", "")
    }, ensure_ascii=False)


@tool
def get_task_detail(user_openid: str, task_id_or_title: str) -> str:
    """Get task detail by ID or title. User must be creator, assignee, or admin."""
    candidates = _find_task_candidates(task_id_or_title)
    if len(candidates) > 1:
        visible = []
        for item in candidates[:5]:
            auth = authorize(user_openid, "get_task_detail", item)
            if auth.allowed:
                visible.append({
                    "id": str(item["id"]).zfill(3),
                    "title": item["title"],
                    "status": item["status"],
                    "due_date": item.get("due_date", ""),
                })
        if len(visible) > 1:
            return json.dumps({"error": "AMBIGUOUS", "candidates": visible}, ensure_ascii=False)
        if len(visible) == 1:
            task_id = int(visible[0]["id"])
            task = get_task(task_id)
        else:
            return json.dumps({"error": "UNAUTHORIZED", "reason": "你没有权限查看匹配到的任务。"}, ensure_ascii=False)
    else:
        task = candidates[0] if candidates else None

    if not task:
        return "NOT_FOUND"
    auth = authorize(user_openid, "get_task_detail", task)
    if not auth.allowed:
        return json.dumps({"error": "UNAUTHORIZED", "reason": auth.reason}, ensure_ascii=False)
    return json.dumps({
        "id": str(task["id"]).zfill(3),
        "title": task["title"],
        "description": task.get("description", ""),
        "status": task["status"],
        "assignee_openid": task.get("assignee_openid", ""),
        "creator_openid": task.get("creator_openid", ""),
        "due_date": task.get("due_date", ""),
        "created_at": task.get("created_at", ""),
        "completed_at": task.get("completed_at", ""),
    }, ensure_ascii=False)


@tool
def complete_task(user_openid: str, task_id_or_title: str) -> str:
    """Mark a task as done (assignee marks their own task complete). Returns task info or NOT_FOUND."""
    import json
    task = _find_task(task_id_or_title, user_openid)
    if not task:
        return "NOT_FOUND"
    auth = authorize(user_openid, "complete_task", task)
    if not auth.allowed:
        return json.dumps({"error": "UNAUTHORIZED", "reason": auth.reason}, ensure_ascii=False)
    old_status = task["status"]
    update_task_status(task["id"], "verified")
    add_task_event(task["id"], user_openid, "complete_task", old_status, "verified")
    return json.dumps({"id": str(task["id"]).zfill(3), "title": task["title"], "status": "verified"}, ensure_ascii=False)


@tool
def verify_task(user_openid: str, task_id_or_title: str) -> str:
    """Verify/accept a completed task (creator confirms).
    If task_id_or_title is empty, auto-find the user's own tasks that are verified."""
    import json
    task = None
    if task_id_or_title and task_id_or_title.strip():
        task = _find_task(task_id_or_title.strip())
    else:
        candidates = []
        for t in get_all_tasks():
            if t["status"] != "verified":
                continue
            if t.get("creator_openid", "") == user_openid or is_admin(user_openid):
                candidates.append(t)
        if len(candidates) == 1:
            task = candidates[0]
        elif len(candidates) > 1:
            return json.dumps({
                "error": "AMBIGUOUS",
                "candidates": [
                    {"id": str(t["id"]).zfill(3), "title": t["title"]}
                    for t in candidates[:5]
                ]
            }, ensure_ascii=False)

    if not task:
        return "NOT_FOUND"
    auth = authorize(user_openid, "verify_task", task)
    if not auth.allowed:
        return json.dumps({"error": "UNAUTHORIZED", "reason": auth.reason}, ensure_ascii=False)
    if task["status"] != "verified":
        return json.dumps({"error": "NOT_VERIFIED", "current_status": task["status"]}, ensure_ascii=False)
    old_status = task["status"]
    update_task_status(task["id"], "completed")
    add_task_event(task["id"], user_openid, "verify_task", old_status, "completed")
    return json.dumps({"id": str(task["id"]).zfill(3), "title": task["title"], "status": "completed"}, ensure_ascii=False)


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
    """Find task by T00X ID, raw numeric ID, title keyword, or user's latest"""
    if not keyword:
        return None
    tid = keyword.strip().upper()
    # T00X format
    if tid.startswith("T") and tid[1:].isdigit():
        return get_task(int(tid[1:]))
    # Pure numeric ID (e.g. "5" returned by tool)
    if tid.isdigit():
        return get_task(int(tid))
    # Title keyword
    if keyword:
        task = get_task_by_title(keyword)
        if task:
            return task
    # Fallback: user's latest pending task
    if user_openid:
        tasks = query_user_tasks(user_openid)
        if tasks:
            return tasks[0]
    return None


def _find_task_candidates(keyword: str) -> list[dict]:
    """Find candidate tasks by exact ID or fuzzy title."""
    if not keyword:
        return []
    tid = keyword.strip().upper()
    if tid.startswith("T") and tid[1:].isdigit():
        task = get_task(int(tid[1:]))
        return [task] if task else []
    if tid.isdigit():
        task = get_task(int(tid))
        return [task] if task else []
    keyword = keyword.strip()
    if not keyword:
        return []
    matches = []
    for task in get_all_tasks():
        title = task.get("title", "")
        if keyword == title or keyword in title or title in keyword:
            matches.append(task)
    return matches


TASK_TOOLS = [create_task, get_task_status, get_task_detail, complete_task, verify_task, query_my_tasks]


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
