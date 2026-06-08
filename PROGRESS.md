# CommuFlow 开发进度追踪

最后更新：2026-06-08

---

## Phase 1：MVP 核心

### 环境搭建
- [x] Git 初始化 + 远程仓库关联
- [x] 项目目录骨架
- [x] 安装 Python 依赖
- [x] 创建 .env + 配置 DeepSeek
- [ ] 飞书应用创建与配置（App ID / Secret / 事件订阅 / 权限）

### 数据层（db/）
- [x] SQLite 建表（tasks 表 + task_counter）
- [x] 任务 CRUD（创建/查询/状态更新/逾期扫描）
- [x] 本地数据库测试通过

### 飞书 SDK 封装（feishu/）
- [x] 获取 tenant_access_token
- [x] 查询用户信息 / 按姓名搜索用户
- [x] @用户 格式化
- [ ] 飞书消息收发联调

### 意图识别（bot/router.py + bot/llm.py）
- [x] LLM 意图分类（5/5 准确率）
- [x] 低置信度降级回复
- [x] 路由分发到 5 个处理器

### 任务创建（bot/task.py）
- [x] 实体抽取（title/assignee/due_date/description）
- [x] 完整性校验（缺字段 -> 反问模板）
- [x] 用户姓名 -> open_id 映射
- [ ] 端到端测试（需飞书联调）

### 任务状态流转（bot/task.py）
- [x] 完成识别："T001 已完成" -> 待验收
- [x] 验收通过/驳回重做
- [x] 进度查询
- [x] 本地测试通过

### 知识问答（bot/knowledge.py）
- [x] 5 篇内置 SOP 知识库
- [x] 中文 bigram 关键词匹配
- [x] LLM 增强回答（标注来源，已验证准确）

### 会议纪要（bot/meeting.py）
- [x] LLM 结构化纪要生成
- [x] 待办事项表格提取（已验证准确）

### 定时催办（scheduler.py）
- [x] 每 4 小时扫描逾期任务逻辑
- [ ] 联调飞书消息推送

### Flask 入口（main.py）
- [x] /feishu/event 事件回调
- [x] URL 验证（challenge）
- [ ] 飞书开放平台配置回调地址 + 验证通过

---

## 已确认可工作的模块
| 模块 | 状态 |
|------|------|
| SQLite CRUD | ✅ |
| 意图识别 5/5 | ✅ |
| 知识问答（含来源标注） | ✅ |
| 会议纪要 + 待办提取 | ✅ |
| 任务状态流转 | ✅ |
| 实体抽取 | ⚠️ 偶发 JSON 解析问题 |

## 下一步
1. 修复实体抽取偶发 JSON 空值问题
2. 创建飞书应用 + 配置事件回调
3. 端到端联调