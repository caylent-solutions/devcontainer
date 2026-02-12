# [F1.2] Template System

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F1.2 |
| **Status** | in-queue |
| **Parent** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Overhaul of the template system: shared validation function, rewritten create/load/upgrade commands. The template validation system (`validate_template()`) is the cornerstone — it is called by every command that reads a template.

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S1.2.1 | Template Validation System | in-queue | S1.1.2, S1.1.3 |
| S1.2.2 | Template Create Command | in-queue | S1.2.1, S1.1.6, S1.3.1 |
| S1.2.3 | Template Load Command | in-queue | S1.2.1, S1.1.5 |
| S1.2.4 | Template Upgrade Command | in-queue | S1.2.1 |

## Acceptance Criteria (Feature-Level)

- [ ] All 4 stories completed and accepted
- [ ] validate_template() shared function with full structural, key, and auth validation
- [ ] Template create full 17-step prompt sequence with all constraints
- [ ] Template load generates both files via write_project_files()
- [ ] Template upgrade modifies template only, projects sync on next code run
- [ ] All v1.x templates rejected with clear migration error
- [ ] All tests pass, 90%+ unit test coverage

## Log

_(No work has started on this feature yet)_
