provider "aws" {
  region = var.region
  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/terraform-role"
  }

  default_tags {
    tags = {
      Project   = "ichrisbirch"
      ManagedBy = "Terraform"
    }
  }
}
