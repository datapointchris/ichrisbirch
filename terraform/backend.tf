terraform {
  backend "s3" {
    bucket         = "ichrisbirch-terraform"
    key            = "terraform.tfstate"
    region         = "us-east-2"
    dynamodb_table = "ichrisbirch-terraform-state-locking"
  }
}
