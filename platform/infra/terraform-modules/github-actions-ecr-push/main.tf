data "aws_caller_identity" "current" {}

# GitHub Actions OIDC provider
# Allows GitHub Actions to authenticate via OIDC without long-lived credentials.
# The thumbprint list uses a placeholder value — AWS verifies GitHub's OIDC
# tokens via the root CA, not the thumbprint, but the field is required.
resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}

# IAM role assumable only by this repo's main branch via OIDC
resource "aws_iam_role" "github_actions_ecr_push" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github_actions.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:ref:refs/heads/${var.github_branch}"
        }
      }
    }]
  })
}

# Least-privilege policy: ECR Public push to the specific repository only
resource "aws_iam_role_policy" "ecr_public_push" {
  name = "ecr-public-push"
  role = aws_iam_role.github_actions_ecr_push.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECRPublicRepositoryPush"
        Effect = "Allow"
        Action = [
          "ecr-public:BatchCheckLayerAvailability",
          "ecr-public:InitiateLayerUpload",
          "ecr-public:UploadLayerPart",
          "ecr-public:CompleteLayerUpload",
          "ecr-public:PutImage",
          "ecr-public:DescribeImages",
          "ecr-public:DescribeRepositories",
        ]
        Resource = var.ecr_repository_arn
      },
      {
        Sid    = "ECRPublicAuth"
        Effect = "Allow"
        Action = [
          "ecr-public:GetAuthorizationToken",
        ]
        Resource = "*"
      },
      {
        Sid    = "STSBearerToken"
        Effect = "Allow"
        Action = [
          "sts:GetServiceBearerToken",
        ]
        Resource = "*"
      },
    ]
  })
}
