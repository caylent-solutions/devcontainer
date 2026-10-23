include "root" {
  path = find_in_parent_folders("root.hcl")
}

locals {
  role_name   = "kanon-claude-marketplaces-ci"
  policy_name = "ecr-public-pull"
}

terraform {
  source = "${get_repo_root()}/platform/infra/terraform-modules/ecr-public-pull-policy"
}

# Adopt the policy Ryan added to unblock CI without replacing the role.
generate "import_existing_policy" {
  path      = "imports.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
import {
  to = aws_iam_role_policy.ecr_public_pull
  id = "${local.role_name}:${local.policy_name}"
}
EOF
}

inputs = {
  role_name           = local.role_name
  policy_name         = local.policy_name
  expected_account_id = "136685436188"
}
