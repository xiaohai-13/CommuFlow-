"""Pydantic models for LLM structured output — type-safe action extraction"""
from pydantic import BaseModel, Field
from typing import Literal


class TaskAction(BaseModel):
    """提取出来的单步任务操作"""
    action: Literal["create", "complete", "verify", "query", "clarify", "chat"] = Field(
        description="操作: create=分配任务, complete=标记完成, verify=验收, query=查进度, clarify=信息不全要反问, chat=闲聊"
    )
    task_title: str = Field(default="", description="任务标题，如'竞品分析报告'")
    task_id: str = Field(default="", description="任务编号，如 T018")
    assignee_name: str = Field(default="", description="责任人姓名，如'张三'")
    due_date: str = Field(default="", description="截止日期 YYYY-MM-DD")


class ActionPlan(BaseModel):
    """从用户消息提取的操作计划，支持多步骤"""
    steps: list[TaskAction] = Field(description="要执行的操作步骤")
