terraform {
  backend "s3" {
    bucket         = "ichrisbirch-terraform"
    key            = "dev/terraform.tfstate"
    region         = var.region
    dynamodb_table = var.terraform_state_table_name
  }
}
