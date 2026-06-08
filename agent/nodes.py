import json
from langchain_openai import ChatOpenAI
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from agent.state import AgentState
from agent.tools import create_task_tool, search_knowledge
from agent.rag import retrieve_context

llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL, temperature=0)


def intent_node(state: AgentState) -> dict:
    """Step 1: intent recognition"""
    last_msg = state["messages"][-1]["content"]
    prompt = f"""判断用户意图，只输出一个单词：
- assign: 分配任务（含@某人、完成、负责、跟进）
- knowledge: 知识问答（含流程、规定、怎么做、SOP）
- meeting: 会议纪要（含会议记录、纪要、转录）
- query: 进度查询（含我的任务、未完成、进度）
- complete: 完成任务（含已完成、做完了、T00X）
- chat: 闲聊/其他

用户消息：{last_msg}"""
    result = llm.invoke(prompt).content.strip().lower()
    return {"intent": result}


def extract_node(state: AgentState) -> dict:
    """Step 2: entity extraction for assign tasks"""
    if state["intent"] != "assign":
        return {}
    last_msg = state["messages"][-1]["content"]
    prompt = f"""从用户消息中提取任务信息，返回纯JSON。

用户消息：{last_msg}

返回格式：{{"title":"任务标题","assignee":"责任人姓名","due_date":"YYYY-MM-DD","description":"详细描述","dependency":"依赖关系"}}
若某字段缺失值为空字符串。直接返回JSON，不要markdown。"""
    result = llm.invoke(prompt).content.strip()
    try:
        info = json.loads(result)
    except:
        start = result.find("{")
        end = result.rfind("}")
        info = json.loads(result[start:end+1]) if start >= 0 and end > start else {}
    return {"extracted_info": info}


def tool_node(state: AgentState) -> dict:
    """Step 3: execute tool based on intent"""
    intent = state["intent"]
    last_msg = state["messages"][-1]["content"]

    if intent == "assign":
        info = state.get("extracted_info", {})
        if not info.get("title"):
            return {"final_answer": "任务信息不完整，请补充标题、责任人和截止时间。示例：请@张三 周五前完成竞品分析报告"}
        if not info.get("assignee"):
            return {"final_answer": "请明确任务责任人，使用 @用户名 指定。"}
        if not info.get("due_date"):
            return {"final_answer": "请明确截止时间，如：本周五18:00。"}
        result = create_task_tool.invoke({
            "title": info["title"],
            "assignee": info["assignee"],
            "due_date": info["due_date"],
            "description": info.get("description", "")
        })
        return {"final_answer": f"任务「{info['title']}」已创建\n责任人：{info['assignee']}\n截止时间：{info.get('due_date', '')}\n完成后请回复「{info['title']} 已完成」"}

    elif intent == "knowledge":
        docs = retrieve_context(last_msg)
        if not docs:
            return {"final_answer": "未找到相关知识，已记录您的需求。"}
        ctx = "\n---\n".join(docs)
        prompt = f"""根据知识库内容回答问题。标注来源。若无答案说"未找到"。

知识库：{ctx}
问题：{last_msg}"""
        answer = llm.invoke(prompt).content
        return {"final_answer": answer}

    elif intent == "query":
        from utils.task_manager import query_user_tasks
        tasks = query_user_tasks(state["user_id"])
        if not tasks:
            return {"final_answer": "你没有未完成的任务。"}
        lines = ["你的未完成任务："]
        for t in tasks[:10]:
            lines.append(f"  [{t['status']}] T{t['id']:03d} {t['title']} 截止:{t.get('due_date','')}")
        return {"final_answer": "\n".join(lines)}

    elif intent == "meeting":
        prompt = f"""将以下会议记录整理成结构化纪要：

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
        minutes = llm.invoke(prompt).content
        return {"final_answer": minutes}

    elif intent == "complete":
        from utils.task_manager import get_task_by_title, update_task_status
        task = get_task_by_title(last_msg.replace("已完成", "").replace("做完了", "").strip())
        if task:
            update_task_status(task["id"], "completed")
            return {"final_answer": f"任务 T{task['id']:03d}「{task['title']}」已标记完成。"}
        return {"final_answer": "未识别任务ID，请提供任务标题或编号"}

    else:
        answer = llm.invoke(last_msg).content
        return {"final_answer": answer}