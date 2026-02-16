# ECR Public Image Mirror — Infrastructure

## Why This Exists

The devcontainer base image is hosted on Microsoft Container Registry (MCR) at `mcr.microsoft.com/devcontainers/base`. MCR distributes images through Azure CDN, which has limited presence in certain regions — notably parts of South America, Africa, and Southeast Asia. Developers in these regions experience image pull times that can make container startup impractical, since Azure CDN must route requests to distant Points of Presence (POPs).

Amazon ECR Public uses Amazon CloudFront as its CDN, which has broader global edge coverage including regions underserved by Azure CDN. By mirroring the devcontainer base image to ECR Public, developers worldwide get consistent, low-latency image pulls regardless of their geographic location.

The mirror lives at:

```
public.ecr.aws/g0u3p4x2/caylent-solutions/devcontainer-base
```

## Architecture

```
mcr.microsoft.com/devcontainers/base
        |
        | (GitHub Actions scheduled mirror workflow)
        v
public.ecr.aws/g0u3p4x2/caylent-solutions/devcontainer-base
        |
        | (CloudFront global edge network)
        v
   Developer pulls
```

### AWS Resources

| Resource | Value |
|----------|-------|
| **Account** | Caylent Solutions Platform prod (see `aws sts get-caller-identity`) |
| **Region** | `us-east-1` (ECR Public is only available in us-east-1) |
| **ECR Public Registry Alias** | `g0u3p4x2` |
| **Repository** | `caylent-solutions/devcontainer-base` |
| **Repository URI** | `public.ecr.aws/g0u3p4x2/caylent-solutions/devcontainer-base` |
| **Terraform State Bucket** | `caylent-solutions-devcontainer-terraform-state` |
| **State Key** | `us-east-1/ecr-public-repository/terraform.tfstate` |

### Directory Structure

```
platform/
  infra/
    Makefile                              # Terragrunt operation targets
    README.md                             # This file
    terraform-modules/
      ecr-public-repository/
        main.tf                           # aws_ecrpublic_repository resource
        variables.tf                      # Module inputs
        outputs.tf                        # Module outputs
      github-actions-ecr-push/
        main.tf                           # OIDC provider, IAM role, push policy
        variables.tf                      # Module inputs
        outputs.tf                        # Module outputs (role_arn)
    terragrunt/
      root.hcl                            # Remote state (S3) and provider config
      terragrunt.hcl                      # Sentinel file (stops parent search)
      us-east-1/
        ecr-public-repository/
          terragrunt.hcl                  # ECR Public repository
        github-actions-ecr-push/
          terragrunt.hcl                  # OIDC + IAM role for GitHub Actions
```

## Prerequisites

### Tools

Install via `asdf` (versions pinned in `.tool-versions` at repo root):

- **terraform** 1.14.5
- **terragrunt** 0.99.2
- **AWS CLI** v2

### AWS Authentication

You must have an active SSO session for the `platform-prod-admin` profile:

```bash
aws sso login --profile platform-prod-admin
```

**Terraform 1.14.x cannot resolve AWS SSO profiles directly in the S3 backend configuration.** Before running any terraform/terragrunt command, you must export explicit credentials:

```bash
export AWS_PROFILE=platform-prod-admin
eval $(aws configure export-credentials --format env)
unset AWS_PROFILE
```

This sets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` as environment variables. All terragrunt/terraform commands in the current shell session will use these credentials.

To verify authentication:

```bash
aws sts get-caller-identity
# Should show the Caylent Solutions Platform prod account
```

## Operations

All commands are run from `platform/infra/`.

### View Available Targets

```bash
make help
```

### Initialize Backend

Initializes the Terraform backend (S3 state) and downloads providers:

```bash
make init MODULE=ecr-public-repository
```

### Preview Changes

Generates an execution plan showing what Terraform will create, modify, or destroy:

```bash
make plan MODULE=ecr-public-repository
```

Review the plan output carefully before applying.

### Apply Changes

Applies the Terraform plan to create or update resources:

```bash
make apply MODULE=ecr-public-repository
```

Terraform will show the plan and prompt for confirmation before making changes.

### View Outputs

Shows the current Terraform outputs (repository URI, ARN, registry ID):

```bash
make output MODULE=ecr-public-repository
```

### Destroy Resources

Destroys all resources managed by the module. **Use with extreme caution** — this deletes the ECR Public repository and all images in it:

```bash
make destroy MODULE=ecr-public-repository
```

Terraform will show what will be destroyed and prompt for confirmation.

### Format Configuration

Formats all Terraform and Terragrunt HCL files:

```bash
make fmt
```

### Validate Configuration

Validates the Terragrunt/Terraform configuration without applying:

```bash
make validate-config MODULE=ecr-public-repository
```

### Clean Caches

Removes `.terragrunt-cache` and `.terraform` directories:

```bash
# Preview what will be removed
make clean-cache DRY_RUN=1

# Actually remove
make clean-cache
```

## Common Workflows

### First-Time Setup

If you are setting up this infrastructure for the first time in a new AWS account or after a full destroy:

```bash
# 1. Authenticate
aws sso login --profile platform-prod-admin
export AWS_PROFILE=platform-prod-admin
eval $(aws configure export-credentials --format env)
unset AWS_PROFILE

# 2. Navigate to infra directory
cd platform/infra

# 3. Initialize and apply
make init MODULE=ecr-public-repository
make plan MODULE=ecr-public-repository
make apply MODULE=ecr-public-repository

# 4. Verify deployment
make output MODULE=ecr-public-repository
```

### Updating Repository Configuration

To change the repository's catalog data (description, architectures, operating systems):

1. Edit `terragrunt/us-east-1/ecr-public-repository/terragrunt.hcl` — update the `inputs` block
2. Run:
   ```bash
   make plan MODULE=ecr-public-repository   # Review changes
   make apply MODULE=ecr-public-repository  # Apply changes
   ```

### Updating the Terraform Module

To change the Terraform resource definition (adding tags, lifecycle rules, etc.):

1. Edit files in `terraform-modules/ecr-public-repository/`
2. Run:
   ```bash
   make fmt                                 # Format changes
   make plan MODULE=ecr-public-repository   # Review changes
   make apply MODULE=ecr-public-repository  # Apply changes
   ```

### Adding a New Module

To add a new Terraform module (for example, an IAM role):

1. Create the module directory:
   ```
   terraform-modules/
     new-module-name/
       main.tf
       variables.tf
       outputs.tf
   ```

2. Create the Terragrunt child config:
   ```
   terragrunt/
     us-east-1/
       new-module-name/
         terragrunt.hcl
   ```

3. The child `terragrunt.hcl` should follow the existing pattern:
   ```hcl
   include "root" {
     path = find_in_parent_folders("root.hcl")
   }

   terraform {
     source = "${get_repo_root()}/platform/infra/terraform-modules/new-module-name"
   }

   inputs = {
     # module-specific inputs
   }
   ```

4. Run `make plan MODULE=new-module-name` to validate.

### Disaster Recovery

If the ECR Public repository is accidentally deleted:

1. The Terraform state in S3 will show the resource as needing recreation
2. Run `make plan MODULE=ecr-public-repository` to confirm the recreation plan
3. Run `make apply MODULE=ecr-public-repository` to recreate
4. The GitHub Actions mirror workflow will re-push images on its next scheduled run
5. The repository URI and alias will remain the same (tied to the AWS account's ECR Public registry)

**Note:** Image tags will be lost on repository deletion. The mirror workflow repopulates them, but there may be a brief period where pulls fail until the next mirror run completes.

### State Management

Terraform state is stored remotely in S3:

- **Bucket:** `caylent-solutions-devcontainer-terraform-state`
- **Region:** us-east-1
- **Encryption:** AES256 server-side encryption
- **Versioning:** Enabled (allows state recovery)
- **Locking:** Native S3 lock files (`use_lockfile = true`)

To inspect state directly (rarely needed):

```bash
cd platform/infra/terragrunt/us-east-1/ecr-public-repository
terragrunt state list
terragrunt state show aws_ecrpublic_repository.this
```

## Troubleshooting

### "403 Forbidden" on `terragrunt init`

**Cause:** AWS SSO profile cannot be resolved by Terraform's S3 backend.

**Fix:** Export explicit credentials before running any command:
```bash
export AWS_PROFILE=platform-prod-admin
eval $(aws configure export-credentials --format env)
unset AWS_PROFILE
```

### "NoSuchBucket" during bootstrap

**Cause:** Terragrunt 0.99.2 has a race condition in its S3 bucket bootstrap — it checks bucket access before creation completes.

**Fix:** The S3 bucket `caylent-solutions-devcontainer-terraform-state` was pre-created. If it was deleted, recreate it manually:
```bash
aws s3api create-bucket \
  --bucket caylent-solutions-devcontainer-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket caylent-solutions-devcontainer-terraform-state \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket caylent-solutions-devcontainer-terraform-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws s3api put-public-access-block \
  --bucket caylent-solutions-devcontainer-terraform-state \
  --public-access-block-configuration \
  'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'
```

### Shell CWD corruption after cache cleanup

**Cause:** Running `find ... -exec rm -rf {} +` while the shell's working directory is inside a `.terragrunt-cache` directory.

**Fix:** Always use `make clean-cache` from the `platform/infra/` directory, which handles this safely. If your shell becomes corrupted, start a new terminal session.

### Expired SSO credentials

**Cause:** AWS SSO session tokens expire (typically after 1-8 hours depending on configuration).

**Fix:** Re-authenticate and re-export:
```bash
aws sso login --profile platform-prod-admin
export AWS_PROFILE=platform-prod-admin
eval $(aws configure export-credentials --format env)
unset AWS_PROFILE
```

## GitHub Actions Integration

The mirror workflow (`.github/workflows/mirror-devcontainer-image.yml`) authenticates to AWS via OIDC using the `github-actions-ecr-push` module:

- **IAM role:** `github-actions-ecr-public-push` — retrieve ARN via `make output MODULE=github-actions-ecr-push`
- **OIDC provider:** `token.actions.githubusercontent.com`
- **Trust policy:** Scoped to `caylent-solutions/devcontainer` repo, `main` branch only
- **Permissions:** Least-privilege ECR Public push (no admin, no delete)
- **Role ARN:** Stored in GitHub Actions repository variable `ECR_PUSH_ROLE_ARN`

The workflow runs on a semi-monthly schedule (1st and 15th at 6 AM UTC) and supports manual dispatch via the GitHub UI or API.

### Current Image Status

The ECR Public mirror is live with the following tags:

```bash
# Pull the latest mirrored image
docker pull public.ecr.aws/g0u3p4x2/caylent-solutions/devcontainer-base:noble

# List available tags
aws ecr-public describe-images \
  --repository-name caylent-solutions/devcontainer-base \
  --region us-east-1 \
  --query 'imageDetails[].imageTags' \
  --output text
```

Tags follow this convention:
- `:noble` — rolling tag, always points to the latest mirrored image
- `:noble-<digest-prefix>` — immutable tag tied to a specific upstream digest (e.g., `noble-3dcb059253b2`)

## Key Values

| Value | How to retrieve |
|-------|----------------|
| `ALIAS` | `g0u3p4x2` (fixed per account registry) |
| `REPOSITORY_URI` | `make output MODULE=ecr-public-repository` |
| `ROLE_ARN` | `make output MODULE=github-actions-ecr-push` |
| `ACCOUNT_ID` | `aws sts get-caller-identity` |
