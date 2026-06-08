# CommuFlow 开发进度追踪

最后更新：2026-06-08

---

## Phase 1：MVP 核心（可收发消息 + 任务闭环）

### 环境搭建
- [x] Git 初始化 + 远程仓库关联
- [x] 项目目录骨架
- [ ] 安装 Python 依赖 (pip install -r requirements.txt)
- [ ] 复制 .env.example -> .env，填入 API Key
- [ ] 飞书应用创建与配置（App ID / Secret / 事件订阅 / 权限）

### 数据层（db/）
- [x] SQLite 建表（tasks 表 + task_counter）
- [x] 任务 CRUD（创建 / 查询 / 状态更新 / 逾期扫描）
- [ ] 本地启动验证数据库

### 飞书 SDK 封装（feishu/）
- [x] 获取 tenant_access_token
- [x] 查询用户信息 / 按姓名搜索用户
- [x] 获取消息内容
- [x] 发送文本消息 / 回复消息
- [x] @用户 格式化
- [ ] 飞书消息收发联调（ngrok 内网穿透 / 公网部署）

### 意图识别（bot/router.py + bot/llm.py）
- [x] LLM 意图分类 prompt（6 种意图）
- [x] 低置信度降级回复
- [x] 路由分发到 5 个处理器
- [ ] 实测意图识别准确率，调优 prompt

### 任务创建（bot/task.py）
- [x] 实体抽取（LLM 提取 title / assignee / due_date / description）
- [x] 完整性校验（缺字段 -> 反问模板）
- [x] 用户姓名 -> open_id 映射
- [x] 任务入库 + 生成确认消息
- [ ] 端到端测试：发消息 -> 收到反问/确认

### 任务状态流转（bot/task.py）
- [x] 完成识别："T001 已完成" -> 状态 -> 待验收
- [x] 验收通过："T001 验收通过" -> 状态 -> 已完成
- [x] 驳回重做："T001 需修改" -> 状态 -> 进行中
- [x] 进度查询："我的任务有哪些"
- [ ] 状态流转完整链路测试

### 知识问答（bot/knowledge.py）
- [x] 5 篇内置 SOP 知识库
- [x] 关键词匹配检索
- [x] LLM 增强回答（标注来源）
- [ ] 扩充企业知识库内容
- [ ] 后续接入 Chroma 向量检索

### 会议纪要（bot/meeting.py）
- [x] LLM 结构化纪要生成
- [x] 待办事项表格提取
- [ ] 实测纪要质量

### 定时催办（scheduler.py）
- [x] 每 4 小时扫描逾期任务逻辑
- [ ] 联调飞书消息推送

### Flask 入口（main.py）
- [x] /feishu/event 事件回调接收
- [x] URL 验证（challenge）
- [x] 消息解析 + 路由 + 回复
- [ ] 飞书开放平台配置回调地址 + 验证通过

---

## Phase 2：增强（RAG + 纪要 + 看板）
- [ ] Chroma 向量数据库接入
- [ ] 文档自动切片入库
- [ ] 知识自动沉淀（任务完成 -> 摘要 -> 入库）
- [ ] Flask 任务看板页面
- [ ] 验收通知优化（卡片消息）

## Phase 3：闭环强化
- [ ] 逾期升级催办（>24h -> @上级）
- [ ] 飞书多维表格同步
- [ ] 飞书任务中心 API 同步
- [ ] 异常重试队列

## Phase 4：多智能体
- [ ] TaskMaster 子智能体
- [ ] KnowledgeKeeper 子智能体
- [ ] 总调度路由

---

## 端到端演示案例

| 步 | 用户行为 | 智能体行为 | 状态 |
|---|---|---|---|
| 1 | @CommuFlow 请生产部把订单#C2024交期提前3天 | 反问缺失信息 | [ ] |
| 2 | 生产@李芳，采购@张伟，截止6月10日 | 创建 2 个任务，@两人 | [ ] |
| 3 | 李芳回复：生产中，没问题 | 更新任务1 -> 已完成 | [ ] |
| 4 | 张伟回复：物料缺，需要5天采购 | 通知 + 更新截止时间 | [ ] |
| 5 | 用户回复：验收通过 | 任务闭环，案例入知识库 | [ ] |

---

## 快捷验证命令

```powershell
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from db.database import init_db; init_db(); print('DB OK')"

# 启动服务
python main.py
```
