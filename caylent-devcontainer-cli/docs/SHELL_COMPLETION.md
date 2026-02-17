# Shell Completion

The Caylent Devcontainer CLI supports tab completion for bash and zsh. Completion covers all commands, subcommands, flags, and flag values (e.g. `--ide vscode|cursor`).

## Prerequisites

### Bash

The persistent completion method (Option 1) requires the `bash-completion` package:

```bash
# macOS (Homebrew)
brew install bash-completion@2

# Ubuntu/Debian
sudo apt install bash-completion
```

Ensure it is sourced in your `~/.bashrc`:

```bash
# macOS (Homebrew)
[[ -r "/opt/homebrew/etc/profile.d/bash_completion.sh" ]] && source "/opt/homebrew/etc/profile.d/bash_completion.sh"

# Linux (usually sourced automatically; if not, add to ~/.bashrc)
[[ -r "/usr/share/bash-completion/bash_completion" ]] && source "/usr/share/bash-completion/bash_completion"
```

If you prefer not to install `bash-completion`, use Option 2 (eval in `.bashrc`) instead.

### Zsh

Zsh includes built-in completion support. No additional packages are required — just ensure `compinit` is called in your `~/.zshrc` (see setup below).

## Setup

### Bash

**Option 1: Persistent (recommended)**

> Requires `bash-completion` — see [Prerequisites](#prerequisites).

```bash
# Generate and install the completion script
cdevcontainer completion bash > ~/.local/share/bash-completion/completions/cdevcontainer
```

If the directory does not exist, create it first:

```bash
mkdir -p ~/.local/share/bash-completion/completions
cdevcontainer completion bash > ~/.local/share/bash-completion/completions/cdevcontainer
```

**Option 2: Add to shell profile**

```bash
echo 'eval "$(cdevcontainer completion bash)"' >> ~/.bashrc
source ~/.bashrc
```

### Zsh

**Option 1: Persistent (recommended)**

```bash
# Create a completions directory if it doesn't exist
mkdir -p ~/.zfunc

# Generate and install the completion script
cdevcontainer completion zsh > ~/.zfunc/_cdevcontainer
```

Ensure `~/.zfunc` is in your `fpath` by adding this to `~/.zshrc` (before `compinit`):

```bash
fpath=(~/.zfunc $fpath)
autoload -Uz compinit && compinit
```

Then reload your shell:

```bash
source ~/.zshrc
```

**Option 2: Add to shell profile**

```bash
echo 'eval "$(cdevcontainer completion zsh)"' >> ~/.zshrc
source ~/.zshrc
```

## Dynamic Template Name Completion

Commands that accept an existing template name (`view`, `edit`, `load`, `delete`, `upgrade`) support dynamic tab completion of template names. The completion script reads template JSON files from `~/.devcontainer-templates/` at tab-press time, so newly created templates are available immediately.

Commands that accept a *new* name (`save`, `create`) do not offer template name suggestions.

## Verifying

After setup, open a new terminal and test:

```bash
# Complete commands
cdevcontainer <TAB>
# Shows: catalog  code  completion  setup-devcontainer  template

# Complete template subcommands
cdevcontainer template <TAB>
# Shows: create  delete  edit  list  load  save  upgrade  view

# Complete flags
cdevcontainer code --<TAB>
# Shows: --help  --ide  --regenerate-shell-env

# Complete flag values
cdevcontainer code --ide <TAB>
# Shows: cursor  vscode

# Complete template names (requires templates in ~/.devcontainer-templates/)
cdevcontainer template view <TAB>
# Shows: my-template  work-profile  ...
```

## Updating

When the CLI is upgraded and new commands or flags are added, regenerate the completion script:

```bash
# Bash
cdevcontainer completion bash > ~/.local/share/bash-completion/completions/cdevcontainer

# Zsh
cdevcontainer completion zsh > ~/.zfunc/_cdevcontainer
```

## Troubleshooting

### Completions not working after setup

- Open a **new terminal window** — completions are loaded at shell startup.
- For zsh, ensure `compinit` is called **after** setting `fpath`.

### Zsh: `command not found: compdef`

Run `compinit` before the completion script is sourced:

```bash
autoload -Uz compinit && compinit
```

### Bash: completions directory not loaded

Ensure `bash-completion` is installed and sourced — see [Prerequisites](#prerequisites).

### Completions are stale after CLI upgrade

Regenerate the completion script using the commands in the [Updating](#updating) section.
