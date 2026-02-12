# [F1.5] Catalog Integration

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F1.5 |
| **Status** | in-queue |
| **Parent** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Integrating the catalog pipeline into existing commands. setup-devcontainer uses the unified catalog flow for all sources. code command reads catalog-entry.json for upgrades.

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S1.5.1 | Setup-DevContainer Catalog Integration | in-queue | S1.4.3, S1.3.4 |
| S1.5.2 | Code Command Catalog Integration | in-queue | S1.4.3, S1.3.3 |
| S1.5.3 | project-setup.sh Lifecycle | in-queue | S1.5.1 |

## Acceptance Criteria (Feature-Level)

- [ ] All 3 stories completed and accepted
- [ ] setup-devcontainer uses unified catalog pipeline for all sources
- [ ] Without DEVCONTAINER_CATALOG_URL: auto-clones this repo, auto-selects default
- [ ] With DEVCONTAINER_CATALOG_URL: source selection, browsing UI
- [ ] --catalog-entry flag skips browsing and selects directly
- [ ] code command reads catalog-entry.json for Step 5 option 1
- [ ] project-setup.sh lifecycle fully implemented
- [ ] All tests pass, 90%+ unit test coverage

## Log

_(No work has started on this feature yet)_
