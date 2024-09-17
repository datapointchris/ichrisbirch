terraform {
  backend "s3" {
    bucket         = "ichrisbirch-terraform"
    key            = "terraform.tfstate"
    region         = var.region
    dynamodb_table = "ichrisbirch-terraform-state-locking"
  }
}
