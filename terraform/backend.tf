terraform {
  backend "s3" {
    bucket         = "ichrisbirch-terraform"
    key            = "prod/terraform.tfstate"
    region         = var.region
    dynamodb_table = var.terraform_state_table_name
  }
}
