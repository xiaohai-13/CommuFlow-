"""TaskAgent"""
from agent.base import create_agent
from agent.tools import TASK_TOOLS

PROMPT = """你是 CommuFlow 任务管理助手。处理用户的任务请求。

规则：
1. 用户要分配任务 → 提取标题、责任人(@用户)、截止时间。缺信息反问用户，不要猜测。
2. 信息齐全 → 用 create_task 创建，回复格式：T00X 任务「标题」已创建\n责任人：{名字}\n截止时间：{日期}\n\n完成后请回复「T00X 已完成」
3. 包含 T00X 的消息 → 先看任务状态：pending → 用 complete_task；verified → 用 verify_task
4. 用户查进度 → 用 query_my_tasks，友好列出
5. 回复必须包含任务ID，引导下一步

当前用户ID: {user_id}"""

executor = create_agent(PROMPT, TASK_TOOLS)


def run(user_id: str, chat_id: str, message: str, mention_map: dict) -> str:
    from agent.base import run_agent
    return run_agent(executor, user_id, chat_id, message, "task")