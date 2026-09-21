terraform {
  # The bucket name carries the account id, so it is passed at init. See docs/terraform.md.
  backend "s3" {
    key          = "ichrisbirch/terraform.tfstate"
    region       = "us-east-2"
    use_lockfile = true
  }
}
