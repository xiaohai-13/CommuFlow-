"""Agent nodes — prompt orchestration, memory, tool routing"""
import json
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from utils.logger import logger
from agent.state import AgentState
from agent.memory import save_message, load_history, get_last_intent
from agent.tools import TOOL_BY_NAME
from agent.rag import retrieve_context
from datetime import datetime
TODAY = datetime.now().strftime("%Y-%m-%d")

SYSTEM_PROMPT = """你是 CommuFlow，企业内部任务管理智能体。严格遵守以下规则：

【身份】你是任务管理助手，不是通用AI。禁止扮演其他AI。

【能力】你只能：创建任务、查询进度、完成任务、知识问答、会议纪要。

【约束】能力范围外的问题统一回复固定话术。回复简洁，直奔主题。信息缺失时反问用户。

【用户】用户ID: {user_id}"""

FALLBACK_REPLY = "我是 CommuFlow 任务助手。可以帮你：\n- 分配任务：请@张三 周五前完成竞品分析\n- 查进度：我的任务有哪些\n- 完成任务：竞品分析 已完成\n- 问流程：紧急订单变更流程是什么"

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)


def intent_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1]["content"]
    chat_id = state["chat_id"]
    user_id = state["user_id"]

    prev = get_last_intent(chat_id)
    if prev and prev["intent"] == "assign" and prev["entities"].get("waiting"):
        return {"intent": "assign_followup"}

    history = load_history(chat_id, limit=4)
    context = ""
    if history:
        context = "对话历史：\n" + "\n".join(
            f"[{h['role']}] {h['content'][:100]}" for h in history[-3:]
        ) + "\n\n"

    prompt = SYSTEM_PROMPT.format(user_id=user_id) + f"""

{context}判断意图，只输出一个单词（assign/knowledge/meeting/query/complete/chat）：
消息：{last_msg}
意图："""

    result = llm.invoke(prompt).content.strip().lower()
    intent = result.split()[0] if result else "chat"
    save_message(chat_id, "user", last_msg, intent=intent)
    return {"intent": intent}


def extract_node(state: AgentState) -> dict:
    intent = state["intent"]
    if intent not in ("assign", "assign_followup"):
        return {}

    chat_id = state["chat_id"]
    last_msg = state["messages"][-1]["content"]
    mention_map = state.get("mention_map", {})
    prev = get_last_intent(chat_id)

    if intent == "assign_followup" and prev:
        prev_entities = prev.get("entities", {})
        missing = prev_entities.get("waiting", "")

        if "时间" in missing or "截止" in missing:
            prompt = f"今天是{TODAY}。提取截止时间，返回JSON：{{\"due_date\":\"YYYY-MM-DD\"}}\n消息：{last_msg}"
            try:
                r = llm.invoke(prompt).content.strip()
                r = r[r.find("{"):r.rfind("}")+1]
                prev_entities.update(json.loads(r))
            except:
                prev_entities["due_date"] = last_msg.strip()

        # Restore mention_map from memory
        saved_map = prev_entities.pop("_mention_map", None)
        if saved_map and not mention_map:
            mention_map = saved_map

        if prev_entities.get("title") and prev_entities.get("assignee") and prev_entities.get("due_date"):
            prev_entities.pop("waiting", None)
            prev_entities["_mention_map"] = mention_map
            save_message(chat_id, "system", json.dumps(prev_entities, ensure_ascii=False),
                        entities=prev_entities, intent="assign")
            return {"extracted_info": prev_entities}

    prompt = f"今天是{TODAY}。提取任务信息，返回JSON：{{\"title\":\"标题\",\"assignee\":\"责任人\",\"due_date\":\"YYYY-MM-DD\",\"description\":\"描述\"}}\n消息：{last_msg}"
    try:
        r = llm.invoke(prompt).content.strip()
        r = r[r.find("{"):r.rfind("}")+1]
        info = json.loads(r)
    except:
        info = {"title": "", "assignee": "", "due_date": "", "description": ""}

    # Store mention_map for follow-up
    info["_mention_map"] = mention_map
    save_message(chat_id, "system", json.dumps(info, ensure_ascii=False), entities=info, intent="assign")
    return {"extracted_info": info}


def tool_node(state: AgentState) -> dict:
    intent = state["intent"]
    last_msg = state["messages"][-1]["content"]
    chat_id = state["chat_id"]
    user_id = state["user_id"]
    mention_map = state.get("mention_map", {})
    info = state.get("extracted_info", {})

    # Restore mention_map from extracted_info (set by extract_node)
    saved_map = info.pop("_mention_map", None)
    if saved_map and not mention_map:
        mention_map = saved_map

    def resolve_assignee(name: str) -> tuple:
        for key, info_item in mention_map.items():
            if info_item["name"] == name:
                return info_item["open_id"], info_item["name"]
        return name, name

    # ── ASSIGN TASK ──
    if intent in ("assign", "assign_followup"):
        title = info.get("title", "")
        assignee = info.get("assignee", "")
        due_date = info.get("due_date", "")
        description = info.get("description", "")

        if not title:
            return {"final_answer": "请问任务具体要做什么？"}
        if not assignee:
            return {"final_answer": "请问该任务的责任人是谁？请 @ 他。"}
        if not due_date:
            entities = {"title": title, "assignee": assignee, "description": description, "waiting": "截止时间", "_mention_map": mention_map}
            save_message(chat_id, "system", json.dumps(entities, ensure_ascii=False), entities=entities, intent="assign")
            return {"final_answer": "请明确截止时间，例如：2026-06-15 或 下周五18:00。"}

        open_id, real_name = resolve_assignee(assignee)
        result = TOOL_BY_NAME["create_task"].invoke({
            "title": title, "assignee_openid": open_id,
            "due_date": due_date, "description": description or ""
        })
        save_message(chat_id, "assistant", result, intent="assign")
        return {"final_answer": f"任务「{title}」已创建\n责任人：{real_name}\n截止时间：{due_date}\n\n完成后请回复「{title} 已完成」"}

    # ── KNOWLEDGE ──
    if intent == "knowledge":
        docs = retrieve_context(last_msg)
        if not docs:
            return {"final_answer": "未找到相关知识，已记录需求，管理员将补充。"}
        ctx = "\n---\n".join(docs)
        prompt = SYSTEM_PROMPT.format(user_id=user_id) + f"\n根据知识库回答，标注来源：\n{ctx}\n问题：{last_msg}"
        answer = llm.invoke(prompt).content
        save_message(chat_id, "assistant", answer, intent="knowledge")
        return {"final_answer": answer}

    # ── QUERY ──
    if intent == "query":
        result = TOOL_BY_NAME["query_my_tasks"].invoke({"user_openid": user_id})
        save_message(chat_id, "assistant", result, intent="query")
        return {"final_answer": result}

    # ── COMPLETE ──
    if intent == "complete":
        is_verify = "验收" in last_msg
        keyword = last_msg.replace("已完成", "").replace("做完了", "").replace("验收通过", "").replace("需修改", "").strip()
        if is_verify and not keyword:
            keyword = "验收"
        result = TOOL_BY_NAME["mark_task_complete"].invoke({"user_openid": user_id, "task_keyword": keyword})
        save_message(chat_id, "assistant", result, intent="complete")
        return {"final_answer": result}

    # ── MEETING ──
    if intent == "meeting":
        prompt = SYSTEM_PROMPT.format(user_id=user_id) + f"\n整理会议纪要：\n{last_msg}"
        result = llm.invoke(prompt).content
        save_message(chat_id, "assistant", result, intent="meeting")
        return {"final_answer": result}

    # ── FALLBACK ──
    save_message(chat_id, "assistant", FALLBACK_REPLY, intent="chat")
    return {"final_answer": FALLBACK_REPLY}
