include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/platform/infra/terraform-modules/ecr-public-repository"
}

inputs = {
  repository_name   = "caylent-solutions/devcontainer-base"
  description       = "Mirror of mcr.microsoft.com/devcontainers/base for global low-latency pulls"
  operating_systems = ["Linux"]
  architectures     = ["x86-64", "ARM 64"]
}
