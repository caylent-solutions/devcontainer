# [F2.1] ECR Infrastructure

## Work Unit Metadata

| Field | Value |
|-------|-------|
| **Type** | Feature |
| **Number** | F2.1 |
| **Status** | in-queue |
| **Parent** | E2 — ECR Public Image Mirror |

## Description

Set up the AWS infrastructure for the ECR Public image mirror. This includes the ECR Public repository, IAM OIDC identity provider for GitHub Actions, and the least-privilege IAM role.

All infrastructure is set up via the developer's authenticated AWS CLI session from this devcontainer.

## Stories

| ID | Name | Status | Dependencies |
|----|------|--------|-------------|
| S2.1.1 | ECR Public Repository Setup | in-queue | None |
| S2.1.2 | IAM OIDC & Role Setup | in-queue | S2.1.1 |

## Acceptance Criteria (Feature-Level)

- [ ] All 2 stories completed and accepted
- [ ] ECR Public repo exists in us-east-1
- [ ] IAM OIDC provider for GitHub Actions configured
- [ ] IAM role with least-privilege ECR Public push policy
- [ ] Trust policy scoped to this repo's main branch
- [ ] No long-lived AWS credentials

## Log

_(No work has started on this feature yet)_
