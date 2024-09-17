provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "ichrisbirch"
      ManagedBy = "Terraform"
    }
  }
}
