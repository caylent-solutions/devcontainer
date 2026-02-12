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
6. **Full functional test coverage** — write functional tests in `tests/functional/` that validate end-to-end behavior. Every story that adds or modifies code MUST have a corresponding functional test file. Do NOT skip this step or claim existing functional tests are sufficient without verifying they exercise the new/modified code paths. If no functional test file exists for the code you changed, create one.
7. **Fix linting and formatting** — run `make lint` and `make format` from `caylent-devcontainer-cli/` (or nested `make` targets) and fix all issues

### Verify Your Work

- After writing a file, read it back to confirm contents match intent
- After running a command, check exit codes and output
- After making changes, run tests to verify behavior
- Run `make test` from `caylent-devcontainer-cli/` to run all tests
- Run `make lint` from `caylent-devcontainer-cli/` to check formatting/style

### Never Bypass Quality Gates

- **Never use `--no-verify`** on any git command
- **Never use `# noqa`, `// nosec`, `@SuppressWarnings`**, or any annotation that silences linters or security scanners
- **Never modify linter/scanner configs to ignore findings**
- If a hook, linter, or security check fails — **fix the root cause**, do not bypass it
- If you believe a finding is a false positive, ask the human — never suppress it yourself

### Update the Log

After each work iteration, update the **Log** section of the work unit file:
- What you completed this session
- What is left to do
- If debugging: what you tried that failed (so future agents don't repeat it) and what worked

---

## Step 5: Validate Acceptance Criteria — One by One

**Before requesting human review, you MUST validate every acceptance criterion individually.**

This is a strict requirement. Do not skip it. Do not batch them. For each criterion:

1. **Read the criterion** from the story's Acceptance Criteria section
2. **Perform a concrete verification** — run a command, read a file, run a test, check coverage, etc.
3. **Record the evidence** — what you checked and what the result was
4. **Check off the criterion** in the story file by changing `- [ ]` to `- [x]`
5. **Move to the next criterion**

### Documentation — Continuously Keep Docs Up to Date

**Documentation must be kept in sync with code changes at all times.** Do not defer documentation updates to later stories or sessions. Every story that changes user-facing behavior, commands, flags, configuration, or version must update documentation in the same commit as the code changes.

Every story has this acceptance criterion:
> Docs updated if project documentation is affected by these changes

This means:
- **Check if any user-facing behavior changed** — commands added/removed/modified, flags changed, configuration changed, version changed
- **Check README.md** (both root and `caylent-devcontainer-cli/README.md`) — does it reference anything that changed? If yes, update it.
- **Check any other docs** (CHANGELOG.md, help text, docstrings, CLI `--help` output) — do they reference anything that changed? If yes, update them.
- **If no documentation exists that references the changes**, note "No documentation references affected" and check it off.
- **If documentation exists and needs updating**, update it BEFORE checking the criterion off.
- **Outdated documentation is worse than no documentation.** Never leave docs that describe removed features, old flags, or old behavior.

### After All Criteria Are Validated

Only after every criterion has been individually verified and checked off:

1. Update the work unit status to `in-review`
2. Update the pointer file to reflect the status change
3. **Request human approval.** Present to the human:
   - The checked-off acceptance criteria (showing each was verified)
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
