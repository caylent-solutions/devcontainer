# Caylent DevContainer CLI v2.0.0 — Agent Execution Prompt

## Instructions

**Do not assume you are the first agent.** Read this prompt fully and follow all instructions before taking any action.

---

## Step 1: Determine Current Work

Read the pointer file:

```
claude-backlog/current-work-unit-in-progress.md
```

This file tells you:
- Which work unit is currently **in-progress** and its file path
- Which work units are **in-queue** next (ordered by priority)

**Only read backlog files as needed.** Do not read every work unit. Start with the pointer file, then read only the active work unit and its parent chain (task -> story -> feature -> epic) to understand context. This keeps your context window small and focused.

---

## Step 2: Read the Active Work Unit

Navigate to the path specified in the pointer file. Read the work unit file (story.md or feature.md). This file contains everything you need:

- Full requirements
- Acceptance criteria
- Definition of ready (dependencies)
- Development workflow (TDD)
- Log of previous work by other agents
- General code requirements

---

## Step 3: Check Definition of Ready

Before starting work, verify all dependencies listed in the "Definition of Ready" section are met:

- Check that blocking work units have status `complete`
- If a dependency is not met, **do not start work**. Instead, update the pointer file to indicate the blocker and note it in the log section.

---

## Step 4: Work the Unit

### Pick Up Where the Last Agent Left Off

Read the **Log** section at the bottom of the work unit file. This tells you:
- What was completed by previous agents
- What is left to do
- What debugging approaches failed (do not repeat these)
- What worked

### Development Workflow (TDD)

All development follows test-driven development:

1. **Write the test first** — write a test that validates the expected behavior
2. **Verify the test fails** — run the test and confirm it fails (red)
3. **Write the code** — implement the minimum code to make the test pass
4. **Verify the test passes** — run the test and confirm it passes (green)
5. **Full unit test coverage** — achieve 90% or greater unit test coverage for the code you wrote
6. **Full functional test coverage** — write functional tests that validate end-to-end behavior
7. **Fix linting and formatting** — run `make lint` and `make format` from `caylent-devcontainer-cli/` (or nested `make` targets) and fix all issues

### Verify Your Work

- After writing a file, read it back to confirm contents match intent
- After running a command, check exit codes and output
- After making changes, run tests to verify behavior
- Run `make test` from `caylent-devcontainer-cli/` to run all tests
- Run `make lint` from `caylent-devcontainer-cli/` to check formatting/style

### Update the Log

After each work iteration, update the **Log** section of the work unit file:
- What you completed this session
- What is left to do
- If debugging: what you tried that failed (so future agents don't repeat it) and what worked

---

## Step 5: Completion — Request Human Review

When you believe the work unit meets all acceptance criteria:

1. Update the work unit status to `in-review`
2. Update the pointer file to reflect the status change
3. **Request human approval.** Present to the human:
   - Summary of what was completed
   - List of files that were modified/created (only files related to this work unit)
   - A proposed git commit message for these changes (no stats, no co-authored-by)
4. **Wait for human approval.** Do not proceed without it.

### On Human Approval

The human will instruct you to:
- Stage only the files related to this work unit (`git add <specific files>`)
- Create the git commit with the approved message
- Push the changes

After push:
- Update the work unit status to `complete`
- Clean up the log section — replace the detailed log with a brief completion note (e.g., "Completed and merged on <date>. All acceptance criteria met.")
- Update the pointer file to point to the next in-queue work unit
- Set the next work unit status to `in-progress`

---

## Step 6: Pick Up Next Work

If the human approves and there are more work units in the queue:
- Read the next work unit from the pointer file
- Continue from Step 2

---

## Work Unit Priority and Scope

- **Pick up work at the feature level** unless the feature is too large for a single session
- If a feature has stories, work through each story sequentially within the feature
- **Every work unit** from epic to story must ultimately be completed, updated, and accepted by the human
- Tasks (below stories) are created only when a story is too large for one session — split it into tasks and work each task sequentially

---

## Key Files

| File | Purpose |
|------|---------|
| `claude-backlog/current-work-unit-in-progress.md` | Pointer to active work |
| `claude-backlog/v2-complete-requirements.md` | Original spec (reference only) |
| `CLAUDE.md` | Project coding standards |
| `caylent-devcontainer-cli/Makefile` | Build/test/lint commands |
| `caylent-devcontainer-cli/src/caylent_devcontainer_cli/` | CLI source code |
| `caylent-devcontainer-cli/tests/` | Unit and functional tests |
