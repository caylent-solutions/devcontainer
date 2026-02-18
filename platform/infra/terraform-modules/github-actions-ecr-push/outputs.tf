output "role_arn" {
  description = "ARN of the IAM role for GitHub Actions to assume"
  value       = aws_iam_role.github_actions_ecr_push.arn
}

output "role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.github_actions_ecr_push.name
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC provider"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}
