---
name: timeout-confirmation
description: 消息确认 + 超时自动推进工作流 — 用于需要用户确认且设置倒计时自动通过的场景
triggers:
  - 发送需要确认的消息时
  - PRD / 技术方案 / 修订意见等确认流程
  - 任何可能阻塞的主流程节点
---

# Timeout Confirmation Workflow

## Trigger Condition

When sending a message that requires user confirmation AND setting an automatic timeout to proceed with a default action if no response is received within the timeout period.

## Workflow

### Step 1: Send Confirmation Request

Send the message to the user with:
1. Clear summary of what needs confirmation
2. Explicit timeout duration (default: 5 minutes)
3. Explicit default action that will be taken on timeout
4. Confirmation request phrasing

Example phrasing:
> [内容摘要]  
> 请确认。如果你[N分钟]内没有回复，我会按"[默认动作]"继续推进，并在提案记录里注明这是超时通过。

### Step 2: Create Countdown Cron Job (CRITICAL - MUST DO IN SAME TURN)

**THIS IS NOT OPTIONAL.** The cron job MUST be created in the same response turn as the confirmation message. Not doing this has caused blocking bugs twice (P-20260422-004, P-20260502-016).

```python
cron(action='create',
     schedule='<current_time + timeout_minutes>',
     prompt='【倒计时到期】提案 P-YYYYMMDD-XXX [事项]确认超时，默认通过处理。请将 [事项] Confirmation 更新为 timeout-approved 并继续[下一步]。',
     name='P-YYYYMMDD-XXX-[事项]-confirm',
     deliver='origin')
```

Common mistake pattern:
- ❌ Wrong: "请确认（超时5分钟默认通过）" → then create cron job in next turn
- ✅ Correct: "请确认（超时5分钟默认通过）" + IMMEDIATELY create cron job in same turn

### Step 3: Record in Proposal

Update the proposal status file:
- Set `XXX Confirmation`: `pending`
- Set `XXX Confirmation Countdown ID`: `<cron_job_id>`

### Step 4: On Timeout Event

When cron fires:
1. Update proposal status: set `XXX Confirmation` to `timeout-approved`
2. Write `Timeout Resolution` note in the proposal
3. Proceed with the default action
4. Clean up the cron job

### Step 5: On User Response (Before Timeout)

When user responds within timeout:
1. If confirmed → update `XXX Confirmation` to `confirmed`, proceed normally
2. If rejected/modified → record new direction, cancel cron job
3. Clean up the cron job

## Standard Timeout Durations

| Context | Default Timeout |
|---------|----------------|
| PRD confirmation | 5 minutes |
| Technical expectations confirmation | 5 minutes |
| General confirmation | 5 minutes |
| Complex technical decision | 10 minutes |

## Key Principles

1. **Cron job must be created in SAME turn as message** — not describing it then creating later; actual execution required in same response
2. **Always set a concrete timeout** — prevents indefinite blocking
3. **Default action must be the historically optimal choice** — not arbitrary
4. **Always update proposal status** — document that timeout occurred
5. **Never ask the same question twice on timeout** — trust the default

## Common Timeout Scenarios

### PRD Confirmation Timeout
→ Default: **Approve and proceed to technical expectations**
→ Reason: User had opportunity to review; silence indicates consent

### Technical Expectations Confirmation Timeout  
→ Default: **Approve with current clear assumptions**
→ Reason: Clear assumptions were stated; user chose not to modify

### Revision Request Timeout
→ Default: **Keep current implementation**
→ Reason: User chose not to provide guidance; dev's current approach stands

## Verification Checklist

- [ ] Cron job CREATED in same turn as confirmation message (NOT described only)
- [ ] Message sent successfully (check delivery confirmation)
- [ ] Cron job created with correct schedule and prompt
- [ ] Proposal status file updated with pending status
- [ ] Timeout event handles all three outcomes (confirm/reject/timeout)
- [ ] Cron job cleaned up after resolution
