# CommuFlow State: Feishu Real-Machine Test Passed

Date: 2026-06-09

Branch purpose:

This branch preserves the current state after the first successful Feishu real-machine test.

## Current Status

Implemented locally:

- Feishu webhook normalization layer.
- TaskAgent Pydantic/JSON action extraction with deterministic tool execution.
- Permission model:
  - admin
  - creator
  - assignee
- Local `roles` table.
- Local `task_events` audit table.
- Task creation permission control.
- Task completion permission control.
- Task verification permission control.
- Task detail query.
- Ambiguous task detail candidate listing.
- Multi-user task isolation.
- RAG knowledge QA.
- Meeting minutes generation.
- Dashboard route at `/dashboard`.

## Local Tests Passed

Commands run:

```powershell
python tests/test_permissions.py
python tests/test_task_detail.py
python tests/test_feishu_flow.py
python tests/test_tools.py
python tests/test_full_pipeline.py
```

Observed result:

- Permission tests passed.
- Task detail tests passed.
- Feishu-flow simulation passed.
- Tool-layer tests passed.
- Full pipeline acceptance test passed.

## Feishu Real-Machine Test

Status: passed.

Verified in a real Feishu group:

- Feishu event delivery through webhook.
- Real bot mention trigger.
- Real user mention normalization.
- `sender.open_id` extraction from actual Feishu event payload.
- Task creation from a real Feishu group message.
- Permission-gated task execution with real Feishu users.
- Dashboard availability after real task creation.

## Required Runtime Setup

Set the real Feishu project manager open_id:

```env
ADMIN_OPENIDS=ou_xxxxxx
```

Then restart:

```powershell
python main.py
```

## Passed Smoke Test Pattern

In the Feishu test group:

1. Project manager sends:
   `@CommuFlow 请@用户033075 2026-06-20前完成后端API开发`

2. Assignee sends:
   `@CommuFlow 我的任务有哪些`

3. Assignee sends:
   `@CommuFlow T00X 已完成`

4. Project manager sends:
   `@CommuFlow T00X 验收通过`

5. Browser opens:
   `http://localhost:5000/dashboard`

Expected:

- Task is assigned to the real mentioned user, not the bot.
- Only assignee can complete.
- Only creator/admin can verify.
- Dashboard reflects final status.
