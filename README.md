# CommuFlow

> 企业内部沟通畅通化智能体 —— 基于 LangChain + LangGraph + 飞书长连接，"沟通即执行"。

## 核心能力

把飞书群聊中的碎片化沟通，自动转化为**可执行任务 → 可跟踪状态 → 可沉淀知识**的完整闭环。

| 意图 | 触发方式 | 行为 |
|------|---------|------|
| 🎯 分配任务 | "@张三 周五前完成竞品分析" | 实体抽取 → 完整性校验 → 创建任务 → @责任人确认 |
| ✅ 完成任务 | "T001 已完成 / 验收通过" | 状态流转 → 通知创建者 → 闭环 |
| 📊 进度查询 | "我的任务有哪些" | 查 SQLite → 返回列表 |
| 📚 知识问答 | "紧急订单变更流程是什么" | Chroma RAG 检索 → LLM 回答（标注来源） |
| 📝 会议纪要 | "生成会议纪要" + 会议记录 | LLM 结构化 → 提取待办 → 一并返回 |
| ⏰ 定时催办 | 每4小时自动扫描 | 逾期任务 @责任人 |

## 项目结构

```
CommuFlow/
├── main.py                  # 飞书长连接入口
├── dashboard.py             # 任务看板
├── agent/
│   ├── graph.py             # LangGraph 状态图
│   ├── nodes.py             # 意图识别/实体抽取/工具调用
│   ├── tools.py             # 自定义工具（任务/知识库/纪要）
│   ├── state.py             # Agent 状态定义
│   └── rag.py               # Chroma RAG 知识库
├── utils/
│   ├── feishu_client.py     # 飞书 API 封装
│   ├── task_manager.py      # SQLite 任务管理
│   ├── config.py            # 配置加载
│   └── logger.py            # 日志
├── knowledge/               # 知识库 Markdown 文档
├── vector_store/            # Chroma 持久化目录
├── data/                    # SQLite 数据库
└── .env                     # 环境变量
```

## 快速开始

```powershell
# 1. 创建环境
conda create -n commuflow python=3.11 -y
conda activate commuflow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env
# 编辑 .env，填入 DeepSeek API Key 和飞书 App 凭证

# 4. 启动长连接（需先创建飞书应用）
python main.py

# 5. 启动看板（可选）
python dashboard.py
```

## 技术栈

| 层次 | 技术 |
|------|------|
| 消息接入 | 飞书 SDK (lark-oapi) 长连接 |
| 智能编排 | LangGraph 状态图 |
| 推理引擎 | DeepSeek (OpenAI 兼容) |
| 向量数据库 | Chroma + bge-small-zh |
| 业务数据库 | SQLite |
| 看板 | Flask |