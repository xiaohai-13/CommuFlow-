# CommuFlow State: Pre Feishu Real-Machine Test

Date: 2026-06-09

Branch purpose:

This branch preserves the current state before Feishu real-machine testing.

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

## Not Yet Done

Feishu real-machine testing has not been completed on this state.

The following must still be verified in a real Feishu group:

- `mentions` normalization with actual bot mention and real user mention.
- `sender.open_id` extraction from actual Feishu event payload.
- `ADMIN_OPENIDS` configuration for the real project manager account.
- Task creation by admin/creator.
- Task creation denial by non-admin.
- Assignee task query.
- Assignee task completion.
- Creator/admin task verification.
- Unauthorized detail access denial.
- Ambiguous task detail query.
- Knowledge QA.
- Meeting minutes.
- `/dashboard` display after real task creation.

## Required Real-Machine Setup

Set the real Feishu project manager open_id:

```env
ADMIN_OPENIDS=ou_xxxxxx
```

Then restart:

```powershell
python main.py
```

## Suggested First Real-Machine Smoke Test

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

