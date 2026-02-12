# Review: Find and Fix Incomplete Replacements of Old Code

## Purpose

This prompt is for a review pass across all code written on the `feature/devcontainer-v2.0.0` branch prior to merging to `main`. The goal is to find instances where old functionality was replaced by new functionality but not all consumers were updated — leaving orphaned references, patched-around tests, or dead code.

## Instructions

### Step 1: Identify All Replaced Functions

Search the git diff between `main` and `HEAD` to find functions/classes that were **deleted** from source files. These are the "old" functions that were replaced.

```bash
git diff main...HEAD -- 'src/**/*.py' | grep '^-def \|^-class ' | grep -v '^---'
```

For each deleted function, note:
- The function name
- The file it was deleted from
- What replaced it (look at the same file's additions)

### Step 2: Search for Orphaned References

For each deleted function name, search the entire codebase:

```bash
grep -rn '<function_name>' src/ tests/
```

Look for:
- **Import statements** that still reference the deleted function (will cause ImportError)
- **Test functions** that test the deleted function directly
- **Mock/patch targets** that reference the old function path
- **Comments or docstrings** that reference the old function name
- **Source inspection tests** (`inspect.getsource`) that check for the old function

### Step 3: Search for Workaround Patterns

Search for patterns that indicate a test was patched around rather than properly updated:

```bash
# Tests that mock the new validation to avoid dealing with it
grep -rn 'detect_validation_issues.*return_value.*_NO_ISSUES' tests/
```

For each such mock, verify:
- Is this test specifically about non-validation behavior? (If so, the mock is appropriate)
- Or was the mock added as a workaround for a test that should have been rewritten?

### Step 4: Verify Test Coverage of New Functions

For each new function that replaced an old one, verify:
- There are dedicated unit tests for the new function
- There are functional tests that exercise the new behavior end-to-end
- The old function's test scenarios are covered by the new tests (not just deleted)

### Step 5: Check for Dead Code

Search for functions that are defined but never called:

```bash
# For each function defined in src/, check if it's called anywhere
grep -rn 'def ' src/ --include='*.py' | while read line; do
    func=$(echo "$line" | sed 's/.*def \([a-zA-Z_]*\).*/\1/')
    count=$(grep -rn "$func" src/ tests/ --include='*.py' | grep -v "def $func" | wc -l)
    if [ "$count" -eq 0 ]; then
        echo "DEAD: $line"
    fi
done
```

### Step 6: Fix Issues

For each issue found:
1. If an old reference exists → update it to use the new function
2. If a test was patched around → rewrite the test properly
3. If dead code exists → delete it
4. If test coverage is missing → add tests for the new function

### Known Replacements to Check

These replacements were made during the v2.0.0 development:

| Old Function | New Function | Story |
|---|---|---|
| `prompt_upgrade_or_continue()` in `code.py` | `_handle_missing_metadata()` + `_handle_missing_variables()` in `code.py` | S1.3.3 |
| Direct `get_missing_env_vars()` usage in `code.py` | `detect_validation_issues()` in `utils/validation.py` | S1.3.3 |
| `generate_shell_env()` in `fs.py` | `write_shell_env()` in `fs.py` | S1.3.2 |
| `write_env_json()` / `write_shell_env_file()` | `write_project_files()` in `fs.py` | S1.1.5 |
| `apply_template()` (multiple versions) | Consolidated `apply_template()` | S1.1.6 |
| `interactive_setup()` (multiple versions) | Consolidated `interactive_setup()` | S1.1.6 |

### Output

After the review, report:
- Number of orphaned references found and fixed
- Number of tests rewritten vs patched
- Number of dead functions removed
- Confirmation that all new functions have proper test coverage
