"""Business authorization for CommuFlow task operations."""
from dataclasses import dataclass
from utils.config import ADMIN_OPENIDS
from utils.task_manager import get_roles


@dataclass
class AuthResult:
    allowed: bool
    reason: str = ""


CREATE_ROLES = {"admin", "creator"}


def is_admin(openid: str, chat_id: str = "") -> bool:
    if openid in ADMIN_OPENIDS:
        return True
    return "admin" in get_roles(openid, chat_id)


def can_create_task(openid: str, chat_id: str = "") -> bool:
    roles = set(get_roles(openid, chat_id))
    if is_admin(openid, chat_id):
        return True
    return bool(roles & CREATE_ROLES)


def authorize(user_id: str, action: str, task: dict | None = None,
              chat_id: str = "") -> AuthResult:
    """Authorize a business action.

    Feishu tells us who the user is. CommuFlow decides what that user may do.
    """
    if is_admin(user_id, chat_id):
        return AuthResult(True)

    if action == "create_task":
        if can_create_task(user_id, chat_id):
            return AuthResult(True)
        return AuthResult(False, "只有管理员或任务创建白名单成员可以创建任务。")

    if not task:
        return AuthResult(False, "未找到任务，无法校验权限。")

    if action == "complete_task":
        if task.get("assignee_openid") == user_id:
            return AuthResult(True)
        return AuthResult(False, "只有任务责任人可以标记完成。")

    if action in {"verify_task", "reject_task", "update_task", "reassign_task", "cancel_task"}:
        if task.get("creator_openid") == user_id:
            return AuthResult(True)
        return AuthResult(False, "只有任务创建者或管理员可以执行该操作。")

    if action == "get_task_detail":
        if task.get("creator_openid") == user_id or task.get("assignee_openid") == user_id:
            return AuthResult(True)
        return AuthResult(False, "你没有权限查看该任务详情。")

    if action == "query_my_tasks":
        return AuthResult(True)

    return AuthResult(False, "未知操作，无法校验权限。")
