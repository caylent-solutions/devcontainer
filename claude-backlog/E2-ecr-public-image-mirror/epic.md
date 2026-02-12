# [E2] ECR Public Image Mirror

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Epic |
| **Number** | E2 |
| **Status** | in-queue |
| **Source Spec** | `claude-backlog/v2-complete-requirements.md` — Work Unit 3 |

## Description

Mirror the Microsoft devcontainer base image (`mcr.microsoft.com/devcontainers/base:noble`) to Amazon ECR Public (`public.ecr.aws`) for global low-latency pulls. The Microsoft image is hosted on Azure which lacks points of presence in South America, causing slow download times.

This epic creates:
- ECR Public repository with global CloudFront distribution
- IAM OIDC provider and least-privilege role for GitHub Actions
- Automated GitHub Actions workflow that polls for upstream changes and mirrors them
- PR-based update flow for devcontainer.json image references

## Features

| ID | Name | Status | Summary |
|----|------|--------|---------|
| F2.1 | ECR Infrastructure | in-queue | ECR Public repo, IAM OIDC provider, IAM role |
| F2.2 | Mirror Automation | in-queue | GitHub Actions workflow, devcontainer.json updates |

## Dependency Order

```
F2.1 (infrastructure) → F2.2 (automation)
S1.4.2 (catalog repo structure) → S2.2.2 (image ref updates need collections/default/devcontainer.json)
```

## Acceptance Criteria (Epic-Level)

- [ ] ECR Public repository exists and is accessible globally
- [ ] IAM OIDC provider configured for GitHub Actions
- [ ] IAM role with least-privilege policy created and trust-scoped to this repo
- [ ] GitHub Actions workflow runs on schedule (semi-monthly: 1st and 15th)
- [ ] Workflow correctly detects upstream image changes via digest comparison
- [ ] Workflow pushes new images to ECR Public only when upstream has changed
- [ ] Workflow creates a PR to update both devcontainer.json files
- [ ] Both devcontainer.json files reference the ECR Public image
- [ ] No long-lived AWS credentials stored in GitHub

## Log

_(No work has started on this epic yet)_
