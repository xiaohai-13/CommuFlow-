import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def classify_intent(text: str) -> dict:
    prompt = f"""分析以下用户消息，判断意图类型。只返回JSON。

用户消息：{text}

意图类型（选一）：
- assign_task: 分配任务、安排工作（关键词：@"某人"、完成、负责、跟进、交给你）
- ask_knowledge: 知识问答（关键词：流程、规定、怎么做、SOP、制度）
- meeting_minutes: 会议纪要（含"会议记录、纪要、转录"等词的长文本）
- query_progress: 进度查询（关键词：我的任务、未完成、进度、有哪些任务）
- complete_task: 完成任务（关键词：已完成、做完了、T00X 已完成、验收）
- chat: 闲聊或其他

返回格式：{{"intent":"intent_type","confidence":0.0-1.0}}"""

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )
        result = json.loads(resp.choices[0].message.content.strip())
        return result
    except Exception:
        return {"intent": "chat", "confidence": 0.3}


def extract_task_entities(text: str) -> dict:
    prompt = f"""从以下用户消息中提取任务信息。如果某字段不存在，值为空字符串。

用户消息：{text}

返回JSON：
{{
    "title": "简短任务标题",
    "assignee": "责任人姓名（不含@符号）",
    "due_date": "截止时间，格式YYYY-MM-DD或YYYY-MM-DD HH:MM",
    "description": "任务详细描述",
    "dependency": "依赖关系描述"
}}"""

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300
        )
        content = resp.choices[0].message.content.strip()
        content = re.sub(r'^`(?:json)?\s*|\s*`$', '', content)
        return json.loads(content)
    except Exception:
        return {"title": "", "assignee": "", "due_date": "", "description": "", "dependency": ""}


def parse_complete_intent(text: str) -> str | None:
    match = re.search(r'T\d{3}', text.upper())
    if match:
        return match.group()
    return None


def ask_llm(prompt: str) -> str:
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM调用失败: {e}]"


def generate_knowledge_answer(question: str, contexts: list[str]) -> str:
    ctx = "\n---\n".join(contexts)
    prompt = f"""根据以下企业知识库内容回答问题。如果知识库中没有相关内容，请如实说明。

知识库内容：
{ctx}

问题：{question}

要求：
1. 基于知识库内容回答，不要编造
2. 标注信息来源（如"根据《XX》第X条"）
3. 如果知识库没有答案，说"未找到相关知识""""

    return ask_llm(prompt)


def generate_meeting_minutes(text: str) -> str:
    prompt = f"""将以下会议记录整理成结构化会议纪要，格式如下：

# 会议纪要
## 会议主题
## 参会人员
## 讨论要点
## 结论
## 待办事项
| 任务 | 责任人 | 截止时间 |
|------|--------|----------|

会议记录：
{text}"""

    return ask_llm(prompt)


def extract_todos_from_minutes(minutes_text: str) -> list[dict]:
    prompt = f"""从以下会议纪要的"待办事项"表格中提取每行，返回JSON数组。

{minutes_text}

返回格式：[{{"task":"任务名","assignee":"责任人","due":"截止时间"}}]
如果没有待办事项，返回空数组 []"""

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500
        )
        content = resp.choices[0].message.content.strip()
        content = re.sub(r'^`(?:json)?\s*|\s*`$', '', content)
        return json.loads(content)
    except Exception:
        return []
