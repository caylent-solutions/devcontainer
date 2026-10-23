terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

data "aws_caller_identity" "current" {}

# Manage only this inline policy; the existing role and its trust are external.
resource "aws_iam_role_policy" "ecr_public_pull" {
  name = var.policy_name
  role = var.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ECRPublicAuth"
        Effect   = "Allow"
        Action   = "ecr-public:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Sid      = "ECRPublicServiceBearerToken"
        Effect   = "Allow"
        Action   = "sts:GetServiceBearerToken"
        Resource = "*"
      },
    ]
  })

  lifecycle {
    precondition {
      condition     = data.aws_caller_identity.current.account_id == var.expected_account_id
      error_message = "Authenticate to the expected AWS account before managing the ECR Public pull policy."
    }
  }
}
