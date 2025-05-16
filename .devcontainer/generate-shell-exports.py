#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import sys
from pathlib import Path

# ===== Logging Helpers =====
def log(level, message):
    colors = {
        "INFO": "\033[0;36m",
        "OK": "\033[0;32m",
        "WARN": "\033[1;33m",
        "ERR": "\033[0;31m",
    }
    reset = "\033[0m"
    print(f"{colors.get(level, '')}[{level}]{reset} {message}", file=sys.stderr)

# ===== Validation =====
def validate_json(data):
    if "containerEnv" not in data or not isinstance(data["containerEnv"], dict):
        raise ValueError("JSON must contain a 'containerEnv' object.")

# ===== Shell Export Generation =====
def generate_exports(env_dict, export_prefix=True):
    lines = []
    for key, value in env_dict.items():
        if isinstance(value, (dict, list)):
            val = json.dumps(value)
        else:
            val = str(value)
        line = f"{'export ' if export_prefix else ''}{key}={shlex.quote(val)}"
        lines.append(line)
    return lines

# ===== .env File Parser =====
def parse_env_file(env_path):
    env = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('\'"')
    return {"containerEnv": env}

# ===== Shell Config Writer =====
def write_shell_source(shell_env_path):
    shell_rc = Path.home() / (".zshrc" if os.environ.get("SHELL", "").endswith("zsh") else ".bashrc")
    line = f"source {shell_env_path}"
    with open(shell_rc, 'a') as rc:
        rc.write(f"\n# Auto-added by generate-shell-exports\n{line}\n")
    log("OK", f"Appended 'source {shell_env_path}' to {shell_rc}")

# ===== Main CLI =====
def main():
    parser = argparse.ArgumentParser(
        description="Generate or convert environment config for devcontainers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command')

    # Subcommand: export
    export_parser = subparsers.add_parser('export', help="Generate shell exports from JSON")
    export_parser.add_argument("json_file", help="Path to JSON with 'containerEnv'")
    export_parser.add_argument("-o", "--output", help="Write to file instead of stdout")
    export_parser.add_argument("--no-export", action="store_true", help="Omit 'export' prefix (for .env files)")
    export_parser.add_argument("--persist", action="store_true", help="Append output file to ~/.bashrc or ~/.zshrc")

    # Subcommand: to-json
    env_parser = subparsers.add_parser('to-json', help="Convert .env file to devcontainer JSON")
    env_parser.add_argument("env_file", help="Path to .env file")
    env_parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")

    args = parser.parse_args()

    if args.command == 'export':
        try:
            with open(args.json_file, "r") as f:
                data = json.load(f)
            validate_json(data)
        except Exception as e:
            log("ERR", f"Error parsing {args.json_file}: {e}")
            sys.exit(1)

        lines = generate_exports(data["containerEnv"], export_prefix=not args.no_export)

        if args.output:
            try:
                with open(args.output, "w") as f:
                    f.write("\n".join(lines) + "\n")
                log("OK", f"Wrote {len(lines)} exports to {args.output}")
                if args.persist:
                    write_shell_source(os.path.abspath(args.output))
            except Exception as e:
                log("ERR", f"Failed to write to {args.output}: {e}")
                sys.exit(1)
        else:
            print("\n".join(lines))

    elif args.command == 'to-json':
        try:
            env_data = parse_env_file(args.env_file)
            json_output = json.dumps(env_data, indent=2)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(json_output + "\n")
                log("OK", f"Wrote JSON to {args.output}")
            else:
                print(json_output)
        except Exception as e:
            log("ERR", f"Failed to convert .env to JSON: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
