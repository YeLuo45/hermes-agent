---
name: dev-delivery-acceptance-checklist
description: Dev agent 交付验收清单 — PM 在标记 delivered 前必须执行的检查流程
---

# Dev Delivery Acceptance Checklist

## Context
When a dev agent (via delegate_task/codex) completes a feature and claims to have delivered, the PM must do a formal acceptance check BEFORE updating proposal status to `delivered`. Dev agents have been observed to:
- Run `npm run build` locally without git committing
- Leave uncommitted changes in working directory
- Introduce runtime bugs that don't show in build output

## Acceptance Checklist

### 1. Git Status Check (REQUIRED)
```bash
cd <project-dir> && git status
```
- [ ] All changes are committed
- [ ] git log shows the feature commit
- [ ] `git log --oneline -3` matches expected deliverable

If there are uncommitted changes → dev has NOT delivered. Do NOT mark as delivered.

### 2. Build Verification
```bash
cd <project-dir> && npm run build
```
- [ ] Exit code 0
- [ ] dist/ files generated

### 3. Code Review (REQUIRED for non-trivial changes)
Quick scan of modified files for:
- [ ] No undefined variable references (e.g., `soundCallbacks` in useGame.js)
- [ ] Correct API signatures (hooks called with correct args)
- [ ] No dead code or commented-out blocks that indicate incomplete work
- [ ] New files are actually created (check with `git status --porcelain`)

### 4. Deployment Verification
- [ ] `git push origin main` succeeds
- [ ] `git push origin main:gh-pages` succeeds
- [ ] `curl -sI <deployment-url> | head -2` returns HTTP 200

### 5. Proposal Status Update
Only update to `delivered` after ALL above checks pass.

## If Bugs Are Found
- If bugs are trivial fixes (typos, missing imports): fix directly and note "PM hotfix applied"
- If bugs are structural/integration issues: revert, reopen `in_dev`, and re-delegate with specific bug report
- Document what was fixed in the acceptance notes

## Pattern: PM as Final Verifier
The dev agent writes code → PM does acceptance check → PM fixes trivial bugs → PM commits/pushes → PM marks delivered.
