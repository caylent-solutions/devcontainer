# [F2.2] Mirror Automation

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F2.2 |
| **Status** | in-queue |
| **Parent** | E2 — ECR Public Image Mirror |

## Description

GitHub Actions workflow for automated image mirroring and devcontainer.json image reference updates.

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S2.2.1 | GitHub Actions Mirror Workflow | in-queue | S2.1.2 |
| S2.2.2 | devcontainer.json Image Reference Updates | in-queue | S2.2.1, S1.4.2 |

## Acceptance Criteria (Feature-Level)

- [ ] All 2 stories completed and accepted
- [ ] Workflow runs on cron (1st and 15th of month) and manual dispatch
- [ ] Digest comparison correctly detects upstream changes
- [ ] Images pushed to ECR Public with noble tag and digest-based version tag
- [ ] PR created automatically when devcontainer.json needs updating
- [ ] Both devcontainer.json files updated consistently

## Log

_(No work has started on this feature yet)_
