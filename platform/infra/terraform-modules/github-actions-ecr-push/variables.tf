variable "github_repository" {
  description = "GitHub repository in 'owner/repo' format (e.g., 'caylent-solutions/devcontainer')"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must be in 'owner/repo' format."
  }
}

variable "github_branch" {
  description = "Branch allowed to assume the IAM role"
  type        = string
  default     = "main"
}

variable "ecr_repository_arn" {
  description = "ARN of the ECR Public repository to grant push access to"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:ecr-public::", var.ecr_repository_arn))
    error_message = "ecr_repository_arn must be a valid ECR Public repository ARN."
  }
}

variable "role_name" {
  description = "Name for the IAM role"
  type        = string
  default     = "github-actions-ecr-public-push"
}
