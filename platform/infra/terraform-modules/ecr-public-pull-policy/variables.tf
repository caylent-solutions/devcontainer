variable "role_name" {
  description = "Existing IAM role that authenticates to ECR Public."
  type        = string
}

variable "policy_name" {
  description = "Inline policy name on the existing IAM role."
  type        = string
}

variable "expected_account_id" {
  description = "AWS account that owns the existing IAM role."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "expected_account_id must be a 12-digit AWS account ID."
  }
}
