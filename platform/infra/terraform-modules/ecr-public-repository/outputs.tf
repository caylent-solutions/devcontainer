output "repository_uri" {
  description = "The URI of the ECR Public repository"
  value       = aws_ecrpublic_repository.this.repository_uri
}

output "repository_arn" {
  description = "The ARN of the ECR Public repository"
  value       = aws_ecrpublic_repository.this.arn
}

output "registry_id" {
  description = "The registry ID (AWS account ID)"
  value       = aws_ecrpublic_repository.this.registry_id
}

output "repository_name" {
  description = "The name of the ECR Public repository"
  value       = aws_ecrpublic_repository.this.repository_name
}
