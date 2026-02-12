# [E1] Caylent DevContainer CLI v2.0.0

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Epic |
| **Number** | E1 |
| **Status** | in-progress |
| **Source Spec** | `claude-backlog/v2-complete-requirements.md` — Work Units 1 and 2 |

## Description

Major rewrite of the Caylent DevContainer CLI from v1.x to v2.0.0. This epic encompasses the CLI core rewrite (DRY refactoring, command rewrites, template system overhaul, breaking changes) and the remote catalog architecture for devcontainer configurations. These are in the same epic because the catalog architecture is integral to the v2.0.0 CLI release.

This is a major release — there is no backward compatibility with v1.x. All v1.x templates must be recreated by the user. The old `env_values` template format is not supported — only `containerEnv`. Python minimum version is `>=3.10`.

## Features

| ID | Name | Status | Summary |
|----|------|--------|---------|
| F1.1 | Core DRY Refactoring & Removals | in-queue | DRY consolidation (spec sections A-M), remove deprecated commands |
| F1.2 | Template System | in-queue | Template validation, create, load, upgrade commands |
| F1.3 | Command Rewrites | in-queue | code, setup-devcontainer, devcontainer.json, postcreate, git auth, UI |
| F1.4 | Catalog Architecture | in-queue | Catalog data model, repo structure, shared functions, CLI commands |
| F1.5 | Catalog Integration | in-queue | Integrate catalog pipeline into setup-devcontainer and code commands |
| F1.6 | Specialized Catalog Repos | in-queue | External catalog repos (Caylent, Smarsh) and documentation |

## Dependency Order

```
F1.1 (foundation) → F1.2 (template system) → F1.3 (commands)
F1.4 (catalog arch) → F1.5 (catalog integration)
F1.1 + F1.4 → F1.5
F1.4 → F1.6
```

## Acceptance Criteria (Epic-Level)

- [ ] All DRY refactoring consolidations implemented (spec sections A-M)
- [ ] All deprecated commands and features removed (env, install/uninstall, bin/cdevcontainer, -y flag)
- [ ] Template system fully rewritten (validate, create, load, upgrade)
- [ ] All main commands rewritten (code, setup-devcontainer)
- [ ] Catalog architecture implemented and integrated
- [ ] Specialized catalog repos created with collections
- [ ] Python >=3.10 in pyproject.toml
- [ ] All v1.x templates rejected with clear migration error
- [ ] All unit and functional tests pass with 90%+ coverage
- [ ] All affected documentation updated

## Log

_(No work has started on this epic yet)_
