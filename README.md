# CommuFlow

> 企业内部沟通畅通化智能体 — "沟通即执行"

基于 LangChain + LangGraph + 飞书长连接的智能助手，将群聊中的自然语言指令自动转化为可执行、可跟踪、可验收的任务闭环。

---

## 架构

```
飞书群聊 @CommuFlow → Flask webhook → 归一化层 → LangGraph 编排
                                           ↓
                        ┌──────────────────┼──────────────────┐
                   TaskAgent         KnowledgeAgent      MeetingAgent
                  Pydantic管线       create_agent        LLM直接生成
                  LLM分类→代码执行    search_sop工具      结构化纪要
                        ↓                  ↓
                   SQLite tasks       Chroma向量库
                   SQLite memory      modelscope下载
```

## 快速开始

### 环境

```bash
conda create -n commuflow python=3.11
conda activate commuflow
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env`，填入：

```env
FEISHU_APP_ID=cli_xxxxxx
FEISHU_APP_SECRET=xxxxxxxx
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

### 构建向量库

```bash
pip install modelscope
python -c "from agent.rag import build_knowledge_base; build_knowledge_base()"
```

### 启动

```bash
# 终端1
python main.py

# 终端2（可选，外网穿透）
ngrok http 5000
```

飞书开放平台 → 事件订阅 → 回调地址：`https://xxx.ngrok-free.dev/feishu/event`

## 功能

| 功能 | 触发示例 | 实现 |
|------|----------|------|
| 分配任务 | `@CommuFlow 请@张三 下周五前完成竞品分析报告` | TaskAgent Pydantic 管线 |
| 查进度 | `@CommuFlow 我的任务有哪些` | query_my_tasks 工具 |
| 完成任务 | `@CommuFlow T001 已完成` | complete_task 工具 |
| 验收任务 | `@CommuFlow T001 验收通过` | verify_task 工具（creator 精确匹配） |
| 知识问答 | `@CommuFlow 紧急订单变更流程是什么` | Chroma RAG + modelscope |
| 会议纪要 | `@CommuFlow 帮我整理会议纪要：...` | LLM 结构化生成 |
| 任务看板 | `http://localhost:5000/dashboard` | Flask 内嵌 |

## 项目结构

```
CommuFlow/
├── main.py                  # Flask webhook + 归一化层 + dashboard
├── dashboard.py             # 独立看板（备用）
├── requirements.txt
├── .env.example
│
├── agent/
│   ├── graph.py             # LangGraph 编排
│   ├── state.py             # AgentState
│   ├── orchestrator.py      # LLM 意图分类
│   ├── schemas.py           # Pydantic ActionPlan/TaskAction
│   ├── task_agent.py        # 任务管线（LLM分类→Pydantic校验→代码执行）
│   ├── knowledge_agent.py   # 知识库 Agent
│   ├── meeting_agent.py     # 会议纪要 Agent
│   ├── tools.py             # 6个工具（create/status/complete/verify/query/search）
│   ├── memory.py            # 对话记忆（chat_id+user_id 复合索引）
│   └── rag.py               # Chroma + modelscope + keyword fallback
│
├── utils/
│   ├── config.py            # 环境变量
│   ├── feishu_client.py     # 飞书 REST API
│   ├── task_manager.py      # SQLite CRUD
│   └── logger.py
│
├── knowledge/               # SOP/FAQ 文档
├── vector_store/            # Chroma 持久化
├── data/                    # SQLite 数据库
│
└── tests/
    ├── test_tools.py        # L0 工具层
    ├── test_orchestrator.py # L1 路由
    ├── test_feishu_flow.py  # L2 飞书流程模拟
    └── test_full_pipeline.py# 全流程5场景
```

## 技术栈

| 组件 | 选型 | 原因 |
|------|------|------|
| LLM | DeepSeek v4-flash | 中文好、便宜 |
| 框架 | LangChain + LangGraph | 状态图编排 |
| 嵌入 | BAAI/bge-small-zh-v1.5 | 中文语义、轻量 |
| 向量库 | Chroma | 本地持久化 |
| 下载 | ModelScope | 国内镜像 |
| 数据库 | SQLite | 零配置 |
| 入口 | Flask + ngrok | 无需公网IP |

## 版本

| Tag | 说明 |
|-----|------|
| `v2.1-demo` | Demo 里程碑：Pydantic 管线 + 归一化层 + 全流程测试 |

## License

MIT
