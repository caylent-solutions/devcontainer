include "root" {
  path = find_in_parent_folders("root.hcl")
}

dependency "ecr" {
  config_path = "../ecr-public-repository"
}

terraform {
  source = "${get_repo_root()}/platform/infra/terraform-modules/github-actions-ecr-push"
}

inputs = {
  github_repository  = "caylent-solutions/devcontainer"
  github_branch      = "main"
  ecr_repository_arn = dependency.ecr.outputs.repository_arn
  role_name          = "github-actions-ecr-public-push"
}
