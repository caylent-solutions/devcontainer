remote_state {
  backend = "s3"

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }

  config = {
    bucket       = "caylent-solutions-devcontainer-terraform-state"
    key          = "${path_relative_to_include()}/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true

    s3_bucket_tags = {
      Name       = "caylent-solutions-devcontainer-terraform-state"
      ManagedBy  = "terragrunt"
      Repository = "caylent-solutions/devcontainer"
    }
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
provider "aws" {
  region = "us-east-1"
}
EOF
}
