# CommuFlow

企业内部沟通畅通化智能体 —— 基于 LangChain + 飞书的"沟通即执行"解决方案。

## 核心能力

把飞书群聊中的碎片化沟通，自动转化为**可执行任务 → 可跟踪状态 → 可沉淀知识**的完整闭环。

| 意图 | 说明 |
|---|---|
| 🎯 分配任务 | @责任人 + 时间 → 自动抽取实体 → 创建任务 → 缺信息反问 |
| ✅ 完成任务 | 回复"T001 已完成" → 更新状态 → 通知验收 → 闭环 |
| 📊 进度查询 | "我的任务有哪些" → 从 SQLite 查询 → 返回列表 |
| 📚 知识问答 | 问流程/SOP → 关键词检索 → LLM 生成回答（标注来源） |
| 📝 会议纪要 | 发送会议记录 → LLM 结构化 → 提取待办 → 一并返回 |
| ⏰ 定时催办 | 每4小时扫描逾期任务 → 自动 @责任人 |

## 项目结构

`
CommuFlow/
├── main.py              # Flask 入口，接收飞书事件
├── config.py            # 环境变量配置
├── scheduler.py         # 定时催办（每4小时）
├── db/                  # SQLite 数据层
├── feishu/              # 飞书 SDK 封装
├── bot/                 # 核心业务逻辑
│   ├── router.py        # 意图路由
│   ├── llm.py           # LLM 调用
│   ├── task.py          # 任务处理器
│   ├── knowledge.py     # 知识问答
│   └── meeting.py       # 会议纪要
└── data/                # SQLite 数据库文件
`

## 快速开始

`powershell
# 1. 配置环境变量
copy .env.example .env
# 编辑 .env，填入飞书 App 凭证和 OpenAI API Key

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python main.py
`

## 技术栈

- **消息接入**: 飞书 SDK (lark-oapi)
- **推理引擎**: OpenAI GPT-4o-mini
- **数据库**: SQLite
- **Web 框架**: Flask
- **定时任务**: APScheduler
