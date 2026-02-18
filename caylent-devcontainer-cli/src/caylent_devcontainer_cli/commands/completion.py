"""Shell completion command for the Caylent Devcontainer CLI."""

import shtab

BASH_PREAMBLE = """\
_cdevcontainer_template_names() {
  local templates_dir="${HOME}/.devcontainer-templates"
  if [ -d "$templates_dir" ]; then
    COMPREPLY=($(compgen -W "$(ls "$templates_dir"/*.json 2>/dev/null | xargs -I{} basename {} .json)" -- "${cur}"))
  fi
}
"""

ZSH_PREAMBLE = """\
_cdevcontainer_template_names() {
  local templates_dir="${HOME}/.devcontainer-templates"
  if [[ -d "$templates_dir" ]]; then
    local -a names
    names=(${templates_dir}/*.json(N:t:r))
    compadd "$@" -- $names
  fi
}
"""

PREAMBLE = {
    "bash": BASH_PREAMBLE,
    "zsh": ZSH_PREAMBLE,
}


def register_command(subparsers, parent_parser=None):
    """Register the completion command.

    Args:
        subparsers: The subparsers object from the parent parser.
        parent_parser: The root ArgumentParser instance. Required so that
            ``shtab.complete()`` can introspect the full command tree.
    """
    completion_parser = subparsers.add_parser(
        "completion",
        help="Generate shell completion script",
    )
    completion_parser.add_argument(
        "shell",
        choices=["bash", "zsh"],
        help="Shell to generate completions for",
    )
    completion_parser.set_defaults(func=handle_completion, _parent_parser=parent_parser)


def handle_completion(args):
    """Handle the completion command by printing the shell completion script."""
    script = shtab.complete(args._parent_parser, args.shell, preamble=PREAMBLE)
    print(script)
