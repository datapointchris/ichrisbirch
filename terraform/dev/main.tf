provider "aws" {
  region = var.region
}

module "vpc" {
  source = "../modules/vpc"
  vpc_cidr = var.vpc_cidr
}

module "ec2" {
  source = "../modules/ec2"
  instance_type = var.instance_type
  ami_id = var.ami_id
  subnet_id = module.vpc.subnet_id
}

module "rds" {
  source = "../modules/rds"
  db_instance_class = var.db_instance_class
  db_name = var.db_name
  db_username = var.db_username
  db_password = var.db_password
  subnet_ids = module.vpc.subnet_ids
}

module "route53" {
  source = "../modules/route53"
  domain_name = var.domain_name
}

module "s3" {
  source = "../modules/s3"
  bucket_name = var.bucket_name
}

module "iam" {
  source = "../modules/iam"
}

module "dynamodb" {
  source = "../modules/dynamodb"
  table_name = var.dynamodb_table_name
}

module "lambda" {
  source = "../modules/lambda"
  function_name = var.lambda_function_name
  handler = var.lambda_handler
  runtime = var.lambda_runtime
  role = module.iam.lambda_role_arn
}
