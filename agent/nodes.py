import json
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.state import AgentState
from agent.tools import create_task_tool
from agent.rag import retrieve_context

SYSTEM_PROMPT = """你是 CommuFlow，一个企业内部任务管理智能体。你只做以下事情：
1. 创建任务：帮用户分配工作任务给指定责任人
2. 查询进度：帮用户查看未完成的任务
3. 完成任务：更新任务状态
4. 知识问答：根据企业内部SOP回答流程问题
5. 会议纪要：将会议记录整理成结构化纪要

对于以上之外的任何问题，简洁回复："我是任务管理助手，可以帮你创建任务、查进度、问流程。请说明你的需求。"不要扮演通用AI，不要闲聊，不要给通用建议。"""

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)

# Simple in-memory conversation context: chat_id -> {"intent": ..., "extracted_info": {...}}
conversation_context = {}


def intent_node(state: AgentState) -> dict:
    chat_id = state["chat_id"]
    last_msg = state["messages"][-1]["content"]
    ctx = conversation_context.get(chat_id, {})

    # If previous intent was "assign" and info was incomplete, this is a follow-up
    if ctx.get("intent") == "assign" and ctx.get("waiting_for"):
        return {"intent": "assign_followup"}

    prompt = f"""{SYSTEM_PROMPT}

判断用户意图，只输出一个单词：
- assign: 分配任务、安排工作（含@某人、请、完成、负责、截止）
- knowledge: 知识问答（含流程、规定、SOP、是什么、怎么做）
- meeting: 会议纪要（含会议记录、纪要、转录）
- query: 进度查询（含我的任务、未完成、进度）
- complete: 完成任务（含已完成、做完了、验收）
- chat: 闲聊或无法识别

用户消息：{last_msg}"""
    result = llm.invoke(prompt).content.strip().lower()
    return {"intent": result}


def extract_node(state: AgentState) -> dict:
    intent = state["intent"]
    if intent not in ("assign", "assign_followup"):
        return {}

    chat_id = state["chat_id"]
    last_msg = state["messages"][-1]["content"]
    ctx = conversation_context.get(chat_id, {})
    prev_info = ctx.get("extracted_info", {})

    if intent == "assign_followup":
        missing = ctx.get("waiting_for", "")
        merged = dict(prev_info)

        # Try to fill the missing field from this message
        if "时间" in missing or "截止" in missing or "due" in missing.lower():
            prompt = f"""从用户消息中只提取截止时间，返回纯JSON：{{"due_date":"YYYY-MM-DD"}}。

用户消息：{last_msg}"""
            try:
                r = llm.invoke(prompt).content.strip()
                r = r[r.find("{"):r.rfind("}")+1]
                merged.update(json.loads(r))
            except:
                merged["due_date"] = last_msg

        # Check if all required fields are now present
        if merged.get("title") and merged.get("assignee") and merged.get("due_date"):
            conversation_context[chat_id] = {}
            return {"extracted_info": merged}
        else:
            still_missing = []
            if not merged.get("title"): still_missing.append("标题")
            if not merged.get("assignee"): still_missing.append("责任人")
            if not merged.get("due_date"): still_missing.append("截止时间")
            conversation_context[chat_id] = {"intent": "assign", "extracted_info": merged, "waiting_for": "、".join(still_missing)}
            return {"extracted_info": merged}
    else:
        prompt = f"""从用户消息中提取任务信息，返回纯JSON。

用户消息：{last_msg}

返回格式：{{"title":"任务标题","assignee":"责任人姓名","due_date":"YYYY-MM-DD","description":"详细描述","dependency":"依赖关系"}}
若某字段缺失值为空字符串。直接返回JSON。"""
        result = llm.invoke(prompt).content.strip()
        try:
            info = json.loads(result)
        except:
            start = result.find("{")
            end = result.rfind("}")
            info = json.loads(result[start:end+1]) if start >= 0 and end > start else {}

    return {"extracted_info": info}


def tool_node(state: AgentState) -> dict:
    intent = state["intent"]
    last_msg = state["messages"][-1]["content"]
    chat_id = state["chat_id"]
    mention_map = state.get("mention_map", {})

    def resolve_assignee(name: str) -> tuple:
        for key, info in mention_map.items():
            if info["name"] == name:
                return info["open_id"], info["name"]
        return name, name

    # ===== ASSIGN TASK =====
    if intent in ("assign", "assign_followup"):
        info = state.get("extracted_info", {})
        if not info.get("title"):
            return {"final_answer": "请问任务具体要做什么？请说明任务标题。"}
        if not info.get("assignee"):
            return {"final_answer": "请问该任务的责任人是谁？请 @ 负责人。"}
        if not info.get("due_date"):
            conversation_context[chat_id] = {"intent": "assign", "extracted_info": info, "waiting_for": "截止时间"}
            return {"final_answer": "请明确截止时间，例如：2026-06-15 或 下周五18:00。"}

        open_id, real_name = resolve_assignee(info["assignee"])
        create_task_tool.invoke({"title": info["title"], "assignee": open_id, "due_date": info["due_date"], "description": info.get("description", "")})
        conversation_context[chat_id] = {}
        return {"final_answer": f"✅ 任务「{info['title']}」已创建\n责任人：{real_name}\n截止时间：{info['due_date']}\n\n完成后请回复「{info['title']} 已完成」"}

    # ===== KNOWLEDGE =====
    elif intent == "knowledge":
        docs = retrieve_context(last_msg)
        if not docs:
            return {"final_answer": "未找到相关知识，已记录您的需求，管理员将补充知识库。"}
        ctx = "\n---\n".join(docs)
        prompt = f"""{SYSTEM_PROMPT}

根据以下企业知识库内容回答用户问题。标注信息来源。若知识库无答案，明确说"未找到"。

知识库：{ctx}
问题：{last_msg}"""
        return {"final_answer": llm.invoke(prompt).content}

    # ===== QUERY PROGRESS =====
    elif intent == "query":
        from utils.task_manager import query_user_tasks
        tasks = query_user_tasks(state["user_id"])
        if not tasks:
            return {"final_answer": "🎉 你没有未完成的任务。"}
        lines = ["📋 你的未完成任务："]
        for t in tasks[:10]:
            lines.append(f"  [{t['status']}] T{str(t['id']).zfill(3)} {t['title']}  截止：{t.get('due_date', '无')}")
        return {"final_answer": "\n".join(lines)}

    # ===== COMPLETE TASK =====
    elif intent == "complete":
        from utils.task_manager import get_task_by_title, update_task_status, query_user_tasks

        clean = last_msg.replace("已完成", "").replace("做完了", "").replace("验收通过", "").replace("需修改", "").strip()
        task = get_task_by_title(clean)
        if task:
            if "验收" in last_msg:
                update_task_status(task["id"], "completed")
                return {"final_answer": f"✅ 任务 T{str(task['id']).zfill(3)}「{task['title']}」验收通过，已闭环。"}
            update_task_status(task["id"], "verified")
            return {"final_answer": f"📋 任务 T{str(task['id']).zfill(3)}「{task['title']}」已标记待验收。\n请创建者回复「验收通过」确认。"}

        tasks = query_user_tasks(state["user_id"])
        if tasks:
            task = tasks[0]
            update_task_status(task["id"], "completed" if "验收" in last_msg else "verified")
            return {"final_answer": f"📋 T{str(task['id']).zfill(3)}「{task['title']}」已更新。"}

        return {"final_answer": "未找到对应任务。请用「任务标题 已完成」格式回复。"}

    # ===== MEETING =====
    elif intent == "meeting":
        prompt = f"""{SYSTEM_PROMPT}

将以下会议记录整理成结构化纪要：

{last_msg}

格式：
# 会议纪要
## 主题
## 参会人员
## 讨论要点
## 结论
## 待办事项
| 任务 | 责任人 | 截止时间 |
|------|--------|----------|"""
        return {"final_answer": llm.invoke(prompt).content}

    # ===== CHAT / UNKNOWN =====
    else:
        return {"final_answer": "我是 CommuFlow 任务管理助手。可以帮你：\n• 🎯 分配任务：「请@张三 周五前完成竞品分析」\n• 📋 查进度：「我的任务有哪些」\n• ✅ 完成任务：「竞品分析 已完成」\n• 📚 问流程：「紧急订单变更流程是什么」\n• 📝 会议纪要：「生成会议纪要」+ 会议记录"}