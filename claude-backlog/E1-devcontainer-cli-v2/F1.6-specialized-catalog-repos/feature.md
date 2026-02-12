# [F1.6] Specialized Catalog Repos

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F1.6 |
| **Status** | in-queue |
| **Parent** | E1 — Caylent DevContainer CLI v2.0.0 |

## Description

Creating the two external catalog repos (Caylent internal, Smarsh client) and comprehensive catalog documentation. Both repos follow the same catalog structure validated by `cdevcontainer catalog validate`.

**Manual prerequisites:** The human must create the GitHub repositories before agents can populate them with content.

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S1.6.1 | Caylent Internal Catalog Repo | in-queue | S1.4.2 + manual prereq |
| S1.6.2 | Smarsh Client Catalog Repo | in-queue | S1.4.2 + manual prereq |
| S1.6.3 | Catalog Documentation | in-queue | S1.6.1, S1.6.2 |

## Acceptance Criteria (Feature-Level)

- [ ] All 3 stories completed and accepted
- [ ] Caylent internal catalog repo populated with structure and docs
- [ ] Smarsh catalog repo with smarsh-java-backend and smarsh-angular-fullstack collections
- [ ] Comprehensive README.md and CONTRIBUTING.md in both catalog repos
- [ ] All catalogs pass `cdevcontainer catalog validate`

## Log

_(No work has started on this feature yet)_
