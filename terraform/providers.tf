provider "aws" {
  region = var.region
  assume_role {
    role_arn = "arn:aws:iam::215933706506:role/TerraformRole"
  }

  default_tags {
    tags = {
      Project   = "ichrisbirch"
      ManagedBy = "Terraform"
    }
  }
}

provider "tls" {}
