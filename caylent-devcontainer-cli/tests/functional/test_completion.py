"""Exercise generated Bash completions through the registered shell function."""

import os
import subprocess

import pytest


@pytest.fixture
def completion_timeout():
    """Bound subprocesses using the test suite's configurable timeout."""
    return float(os.environ.get("TEST_SUBPROCESS_TIMEOUT", "30"))


@pytest.fixture
def bash_completion(tmp_path, completion_timeout):
    """Generate the script using the installed CLI, as a user would."""
    result = subprocess.run(
        ["cdevcontainer", "completion", "bash"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=completion_timeout,
    )
    assert result.stderr == ""
    script = tmp_path / "completion.bash"
    script.write_text(result.stdout)
    return script


@pytest.mark.parametrize(
    ("words", "expected"),
    [
        ([""], {"catalog", "code", "completion", "template", "setup-devcontainer"}),
        (["catalog", ""], {"list", "validate"}),
        (["catalog", "l"], {"list"}),
        (["catalog", "v"], {"validate"}),
        (["catalog", "not-a-subcommand"], set()),
        (["template", ""], {"save", "load", "list", "view", "edit", "delete", "create", "upgrade"}),
        (["code", "--i"], {"--ide"}),
    ],
)
def test_bash_completion_candidates(bash_completion, completion_timeout, words, expected):
    """Validate completion candidates independently of shtab's text formatting."""
    result = subprocess.run(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-e",
            "-c",
            """source "$1"
shift
registration=$(complete -p cdevcontainer)
completion_function=${registration#* -F }
completion_function=${completion_function%% *}
COMP_WORDS=(cdevcontainer "$@")
COMP_CWORD=$((${#COMP_WORDS[@]} - 1))
COMP_LINE="${COMP_WORDS[*]}"
COMP_POINT=${#COMP_LINE}
# Interactive completion functions do not run under errexit. Check their
# final status explicitly so a failed completion still fails this test.
if "$completion_function"; then
  printf '%s\\n' "${COMPREPLY[@]}"
else
  exit "$?"
fi
""",
            "completion-test",
            str(bash_completion),
            *words,
        ],
        cwd=bash_completion.parent,
        capture_output=True,
        text=True,
        check=True,
        timeout=completion_timeout,
    )
    assert result.stderr == ""
    assert set(result.stdout.split()) == expected
