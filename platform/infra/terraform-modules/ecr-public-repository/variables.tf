variable "repository_name" {
  description = "Name of the ECR Public repository"
  type        = string
}

variable "description" {
  description = "Description displayed in the ECR Public Gallery"
  type        = string
  default     = ""
}

variable "operating_systems" {
  description = "Operating systems for ECR Public catalog data"
  type        = list(string)
  default     = ["Linux"]
}

variable "architectures" {
  description = "Architectures for ECR Public catalog data"
  type        = list(string)
  default     = ["x86-64", "ARM 64"]
}
