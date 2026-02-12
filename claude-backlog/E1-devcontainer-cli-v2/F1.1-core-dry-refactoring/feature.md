# [F1.1] Core DRY Refactoring & Removals

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F1.1 |
| **Status** | in-queue |
| **Parent** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

All DRY consolidation work from the spec (sections A through M) and removal of deprecated commands and features. This feature MUST be completed first — all other features in Epic 1 depend on the shared utilities created here.

This feature covers:
- JSON file operations (write_json_file, load_json_config consolidation)
- File path constants centralization
- Template utility functions (get_template_path, get_template_names, ensure_templates_dir, etc.)
- UI and prompt utilities (ask_or_exit, exit_cancelled, exit_with_error)
- Removal of deprecated commands (env, install/uninstall, bin/cdevcontainer, -y flag)
- Project file generation (write_project_files — the core function that generates both JSON and shell.env)
- Template application consolidation (merge duplicate apply_template and interactive_setup functions)
- Import hygiene (module-level imports for sys, COLORS)

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S1.1.1 | JSON & File System Utilities | in-progress | None |
| S1.1.2 | Template Utility Functions | in-queue | None |
| S1.1.3 | UI & Prompt Utilities | in-queue | None |
| S1.1.4 | Remove Deprecated Commands | in-queue | S1.1.3 |
| S1.1.5 | Project File Generation | in-queue | S1.1.1 |
| S1.1.6 | Template Application Consolidation | in-queue | S1.1.5, S1.1.2, S1.1.3 |

## Acceptance Criteria (Feature-Level)

- [ ] All 6 stories completed and accepted
- [ ] All 9 inline json.dump patterns replaced with write_json_file()
- [ ] All 7 inline template path constructions replaced with get_template_path()
- [ ] All 14 inline null-check patterns replaced with ask_or_exit()
- [ ] All ~20 cancellation exit patterns replaced with exit_cancelled()
- [ ] All ~40 inline sys.exit(1) patterns replaced with exit_with_error()
- [ ] env subcommand, install/uninstall commands, bin/cdevcontainer, -y flag all removed
- [ ] write_project_files() generates both JSON and shell.env together with metadata
- [ ] apply_template() and interactive_setup() each merged into single functions
- [ ] All imports at module level (no inline imports)
- [ ] All tests pass, 90%+ unit test coverage

## Log

_(No work has started on this feature yet)_
