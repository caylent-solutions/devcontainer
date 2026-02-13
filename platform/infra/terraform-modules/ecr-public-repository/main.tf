terraform {
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

resource "aws_ecrpublic_repository" "this" {
  repository_name = var.repository_name

  catalog_data {
    description       = var.description
    operating_systems = var.operating_systems
    architectures     = var.architectures
  }
}
