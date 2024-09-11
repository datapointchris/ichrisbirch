# ---------- AWS ---------- #

provider "aws" {
  region = var.region
}

# ---------- DynamoDB ---------- #

module "users_table" {
  source         = "../modules/dynamodb"
  table_name     = var.terraform_state_table_name
  hash_key       = var.terraform_state_hash_key
  hash_key_type  = var.terraform_state_hash_key_type
}

# ---------- EC2 ---------- #

module "ec2" {
  source = "../modules/ec2"
  instance_type = var.instance_type
  ami_id = var.ami_id
  subnet_id = module.vpc.subnet_id
}

# ---------- IAM ---------- #

module "iam" {
  source = "../modules/iam"
}

# ---------- Lambda ---------- #

module "lambda" {
  source = "../modules/lambda"
  function_name = var.lambda_function_name
  handler = var.lambda_handler
  runtime = var.lambda_runtime
  role = module.iam.lambda_role_arn
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
