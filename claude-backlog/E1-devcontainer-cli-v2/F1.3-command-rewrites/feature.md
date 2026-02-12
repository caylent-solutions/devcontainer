# [F1.3] Command Rewrites

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F1.3 |
| **Status** | in-queue |
| **Parent** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Rewriting the main CLI commands (code, setup-devcontainer) and supporting changes (devcontainer.json, postcreate script, git authentication, universal UI).

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S1.3.1 | Universal UI Requirements | in-queue | S1.1.3 |
| S1.3.2 | Code Command Rewrite | in-queue | S1.1.5, S1.1.2 |
| S1.3.3 | Code Command Validation | in-queue | S1.3.2, S1.2.1 |
| S1.3.4 | Setup-DevContainer Rewrite | in-queue | S1.1.5, S1.1.6, S1.3.1 |
| S1.3.5 | devcontainer.json & Postcreate Changes | in-queue | S1.1.5 |
| S1.3.6 | Git Authentication | in-queue | S1.1.5 |

## Acceptance Criteria (Feature-Level)

- [ ] All 6 stories completed and accepted
- [ ] Universal input confirmation on all prompts
- [ ] code command does not source or generate shell.env by default
- [ ] code --regenerate-shell-env regenerates shell.env from existing JSON
- [ ] code validation Steps 0-5 detect and prompt for missing variables
- [ ] setup-devcontainer existing config detection, replace/no-replace flow
- [ ] setup-devcontainer file validation is informational only
- [ ] containerEnv removed from devcontainer.json
- [ ] postCreateCommand sources shell.env first, uses sudo -E
- [ ] Token and SSH git authentication paths fully implemented
- [ ] All tests pass, 90%+ unit test coverage

## Log

_(No work has started on this feature yet)_
