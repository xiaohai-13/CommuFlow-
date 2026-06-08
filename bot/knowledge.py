from bot.llm import generate_knowledge_answer

KNOWLEDGE_BASE = [
    {
        "source": "SOP-001 紧急订单变更SOP 第2条",
        "content": "紧急订单变更需要生产部、采购部、销售部三方确认。生产部评估产能，采购部确认物料，销售部与客户沟通交期。变更审批由生产总监最终批准。"
    },
    {
        "source": "SOP-002 采购流程规范 第5条",
        "content": "常规采购需提前3个工作日提交申请，经部门经理审批后流转至采购部。紧急采购可走绿色通道，由采购总监直接审批，但需事后补交书面说明。"
    },
    {
        "source": "SOP-003 质检标准 第3.2条",
        "content": "产品出库前须通过质检抽检，AQL标准为1.0。不合格批次需全部退回生产线，由生产部填写不合格品处理单，品质部跟进复检。"
    },
    {
        "source": "SOP-004 跨部门协作规范 FAQ",
        "content": "涉及两个以上部门的项目，需在项目启动会上明确各部门接口人和交付时间。日常沟通通过飞书群进行，重要决策需邮件确认留痕。"
    },
    {
        "source": "SOP-005 报销制度 第6条",
        "content": "差旅报销需在返回后5个工作日内提交，附发票和行程单。超过5000元的报销需部门总监加签。加班餐补每人每天不超过50元。"
    },
]


def search_knowledge(question: str, top_k: int = 3) -> list[str]:
    scored = []
    for doc in KNOWLEDGE_BASE:
        content = doc["content"]
        score = 0
        for i in range(len(question) - 1):
            bigram = question[i:i+2]
            if bigram in content:
                score += 1
        score = score / max(len(question) - 1, 1)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, doc in scored[:top_k]:
        if score > 0:
            results.append(f"[{doc['source']}] {doc['content']}")
    return results


def handle_knowledge(text: str, sender_openid: str, sender_name: str, chat_id: str, message_id: str) -> str:
    contexts = search_knowledge(text)
    if not contexts:
        return "未找到相关知识，已记录您的需求，管理员将尽快补充知识库。"

    return generate_knowledge_answer(text, contexts)