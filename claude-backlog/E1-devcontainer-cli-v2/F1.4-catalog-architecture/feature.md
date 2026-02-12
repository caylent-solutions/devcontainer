# [F1.4] Catalog Architecture

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F1.4 |
| **Status** | in-queue |
| **Parent** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Catalog data model, repo structure, shared functions, and CLI catalog commands. Implements the unified catalog-based architecture for all devcontainer configurations from Work Unit 2 of the spec.

Every source of devcontainer files — including this repo's default — follows the same catalog structure. The CLI has one code path for discovering, validating, selecting, and copying devcontainer collections regardless of source.

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S1.4.1 | Catalog Data Model | in-queue | None |
| S1.4.2 | Refactor Repo to Catalog Structure | in-queue | S1.4.1 |
| S1.4.3 | Catalog Shared Functions | in-queue | S1.4.1, S1.1.1 |
| S1.4.4 | Catalog CLI Commands | in-queue | S1.4.3 |
| S1.4.5 | URL Parsing & Error Handling | in-queue | S1.4.3 |

## Acceptance Criteria (Feature-Level)

- [ ] All 5 stories completed and accepted
- [ ] Catalog structure added to this repo (common/devcontainer-assets/, collections/default/)
- [ ] .devcontainer/ untouched (it is this repo's own dev environment)
- [ ] DEFAULT_CATALOG_URL constant in CLI
- [ ] All shared catalog functions implemented (parse, clone, validate, discover, copy)
- [ ] catalog list and catalog validate commands working
- [ ] URL parsing handles all formats including SSH with @ref
- [ ] All error scenarios produce actionable messages
- [ ] All tests pass, 90%+ unit test coverage

## Log

_(No work has started on this feature yet)_
