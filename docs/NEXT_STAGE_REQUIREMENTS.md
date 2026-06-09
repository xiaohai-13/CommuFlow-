# CommuFlow Next Stage Requirements

Last updated: 2026-06-09

This document records the next-stage requirements after the demo milestone. The goal is to evolve CommuFlow from a runnable demo into a safer, more general enterprise workflow assistant.

## 1. Current Demo Scope

The current demo already supports:

- Task creation from Feishu messages.
- My task query.
- Task completion by assignee.
- Task verification by creator.
- Knowledge QA through local RAG.
- Meeting minutes generation.
- A simple Flask task dashboard.
- Feishu webhook message normalization.

The current implementation is good enough for a demo, but still lacks several enterprise controls:

- Permission control.
- Task reference resolution.
- Rejection and rework workflow.
- Task detail query.
- Task modification workflow.
- Audit trail.
- Better dashboard operations.
- More robust meeting action-item creation.

## 2. Core Design Principle

LLM should not directly perform business operations.

Recommended pipeline:

```text
Feishu message
-> message normalization
-> user identity context
-> LLM structured ActionPlan
-> task reference resolution
-> permission authorization
-> state transition validation
-> deterministic tool execution
-> audit log
-> Feishu reply
```

This means:

- LLM extracts intent and entities.
- Python code resolves, checks, and executes.
- SQLite stores task state and audit records.
- Feishu provides identity data, not full business authorization.

## 3. Required Feature Set

### 3.1 Permission Layer

Status: implemented.

Problem:

The current demo assumes all users can create, complete, and verify tasks. In a real Feishu group, different users should have different capabilities.

Required roles:

- Admin: can create, update, verify, reject, reassign, cancel, and view all tasks.
- Creator: the user who created a task; can verify, reject, update, cancel, and view that task.
- Assignee: the user assigned to a task; can view, start, complete, and request delay/reassignment.
- Viewer: normal group member; can only view allowed group/public task summaries.

Suggested local data:

```sql
roles (
  openid TEXT NOT NULL,
  role TEXT NOT NULL,
  scope TEXT DEFAULT 'global',
  chat_id TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

Suggested authorization API:

```python
authorize(user_id: str, action: str, task: dict | None, chat_id: str = "") -> AuthResult
```

Initial policy:

| Action | Allowed Users |
|---|---|
| create_task | admin or creator whitelist |
| complete_task | assignee or admin |
| verify_task | task creator or admin |
| reject_task | task creator or admin |
| update_task | task creator or admin |
| reassign_task | task creator or admin |
| cancel_task | task creator or admin |
| query_my_tasks | current user |
| get_task_detail | creator, assignee, admin |

Acceptance criteria:

- A non-assignee cannot mark another user's task complete.
- A non-creator cannot verify another user's task unless admin.
- Admin open_ids can be configured locally.
- Unauthorized actions return a clear Feishu reply.

### 3.2 Task Detail Query

Status: implemented.

Problem:

Users may ask:

- "T001 任务是什么?"
- "竞品分析报告现在怎么样?"
- "这个任务谁负责?"

Required action:

```text
get_task_detail
```

Required tool:

```python
get_task_detail(task_id_or_title: str, user_openid: str) -> str
```

Returned fields:

- Task ID.
- Title.
- Description.
- Assignee.
- Creator.
- Due date.
- Status.
- Created time.
- Completed time.
- Last updated time.

Acceptance criteria:

- "T001 任务是什么" returns detail.
- "竞品分析报告现在怎么样" returns detail if unique.
- If multiple tasks match, return candidates and ask user to choose.

Implemented coverage:

- `get_task_detail(user_openid, task_id_or_title)` returns task details.
- Creator, assignee, and admin can view task detail.
- Unrelated users are denied.
- Ambiguous title matches return candidate task IDs.
- TaskAgent supports the `detail` action.

### 3.3 Task Reference Resolution

Problem:

Users rarely speak in exact IDs. They may say:

- "那个报告做完了"
- "竞品分析完成了"
- "项目任务已经完成"
- "刚才那个任务验收通过"

Required resolver:

```python
resolve_task_reference(user_id: str, text: str, action: str, chat_id: str) -> ResolveResult
```

Resolution strategy:

1. Exact task ID match: T001.
2. Exact title match.
3. Fuzzy title match among user's relevant tasks.
4. Recent conversation context.
5. Status-aware filtering:
   - complete: assignee's pending/in_progress tasks.
   - verify/reject: creator's verified tasks.
   - detail: tasks visible to current user.
6. If one confident match: proceed.
7. If multiple matches: ask user to choose.
8. If no match: ask for task ID or title.

Acceptance criteria:

- "竞品报告完成了" can resolve to the user's own pending task if unique.
- "验收通过" can resolve to the creator's latest verified task if unique.
- Ambiguous references never mutate task state silently.

### 3.4 Rejection And Rework

Problem:

Enterprise task closure is not always "completed". The creator may reject a submitted task.

Required action:

```text
reject_task
```

Example messages:

- "T001 需修改"
- "T001 验收不通过，数据不完整"
- "竞品报告驳回，补充市场规模"

State transition:

```text
verified -> rejected -> in_progress -> verified -> completed
```

Required fields:

- rejected_reason.
- rejected_by.
- rejected_at.

Acceptance criteria:

- Only creator or admin can reject.
- Rejection reason is saved.
- Assignee can see rejected tasks in "我的任务有哪些".

### 3.5 Task Update

Problem:

Tasks often need deadline changes, title corrections, or assignee changes.

Required actions:

- update_due_date.
- update_title.
- reassign_task.
- cancel_task.

Example messages:

- "T001 截止时间改到6月20日"
- "T001 转给李四"
- "T001 取消"

Acceptance criteria:

- Creator/admin can modify.
- Assignee can request delay but cannot directly change deadline unless admin.
- Changes are recorded in audit log.

### 3.6 Audit Log

Problem:

Enterprise workflows require traceability.

Suggested table:

```sql
task_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER,
  actor_openid TEXT,
  action TEXT,
  old_status TEXT,
  new_status TEXT,
  payload_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

Acceptance criteria:

- Every create/complete/verify/reject/update/cancel action writes an event.
- Dashboard can show recent events.

### 3.7 Dashboard Upgrade

Problem:

Current dashboard only lists tasks.

Required improvements:

- Status filters.
- Assignee filter.
- Overdue highlight.
- Task detail view.
- Recent event timeline.
- Counts by status.

Acceptance criteria:

- Demo can show pending/review/completed tasks clearly.
- Overdue tasks are visually distinct.

### 3.8 Meeting Minutes To Tasks

Problem:

Meeting minutes currently generate text, but do not reliably create tasks.

Required workflow:

1. Generate meeting minutes.
2. Extract action items into structured list.
3. Resolve assignees through mentions or known user mapping.
4. Ask for missing assignees or deadlines.
5. Create tasks after confirmation.

Acceptance criteria:

- Meeting text with clear assignee and deadline creates tasks.
- Missing fields trigger clarification.
- User can choose "只生成纪要，不创建任务".

## 4. Priority Recommendation

Recommended implementation order:

1. Permission Layer.
2. Task Detail Query.
3. Task Reference Resolution.
4. Rejection/Rework.
5. Audit Log.
6. Dashboard Upgrade.
7. Meeting Action Items To Tasks.

Reason:

Permission and reference resolution are foundational. Rejection, update, and dashboard features depend on them.
