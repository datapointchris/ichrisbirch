# ---------- AWS ---------- #

provider "aws" {
  region = var.region
}

# ---------- DynamoDB ---------- #

module "terraform_state_table" {
  source         = "../modules/dynamodb"
  table_name     = var.terraform_state_table_name
  hash_key       = var.terraform_state_hash_key
  hash_key_type  = var.terraform_state_hash_key_type
}

# ---------- EC2 ---------- #

module "ichrisbirch_webserver" {
  source = "../modules/ec2"
  instance_type = var.instance_type
  ami_id = var.ami_id
  subnet_id = module.vpc.subnet_id
  security_group_id = var.security_group_id
}

# ---------- IAM ---------- #

module "iam" {
  source = "../modules/iam"
}



# ---------- RDS ---------- #

module "rds" {
  source = "../modules/rds"
  db_instance_class = var.db_instance_class
  db_name = var.db_name
  db_username = var.db_username
  db_password = var.db_password
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.subnet_ids
}

# ---------- Route 53 ---------- #

module "route53" {
  source = "../modules/route53"
  domain_name = var.domain_name
}

# ---------- S3 ---------- #

module "s3" {
  source = "../modules/s3"
  bucket_name = var.bucket_name
}

# ---------- VPC ---------- #

module "vpc" {
  source = "../modules/vpc"
  vpc_cidr = var.vpc_cidr
}
