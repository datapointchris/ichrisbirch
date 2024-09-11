# ---------- AWS ---------- #

variable "region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-east-2"
}

# ---------- DynamoDB ---------- #

variable "terraform_state_table_name" {
  description = "The name of the terraform state DynamoDB table"
  type        = string
}

variable "terraform_state_hash_key" {
  description = "The hash key for the terraform state DynamoDB table"
  type        = string
}

variable "terraform_state_hash_key_type" {
  description = "The type of the hash key for the terraform state DynamoDB table"
  type        = string
}

# ---------- EC2 ---------- #

variable "instance_type" {
  description = "The type of instance to use"
  type        = string
  default     = "t3.medium"
}

variable "ami_id" {
  description = "The AMI ID to use for the instance"
  type        = string
}

# ---------- Lambda ---------- #

variable "lambda_function_name" {
  description = "The name of the Lambda function"
  type        = string
}

variable "lambda_handler" {
  description = "The handler for the Lambda function"
  type        = string
}

variable "lambda_runtime" {
  description = "The runtime for the Lambda function"
  type        = string
}

# ---------- RDS ---------- #

variable "db_instance_class" {
  description = "The instance class for the RDS instance"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "The name of the RDS database"
  type        = string
}

variable "db_username" {
  description = "The username for the RDS database"
  type        = string
}

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = true
}

# ---------- Route 53 ---------- #

variable "domain_name" {
  description = "The domain name for Route 53"
  type        = string
}

# ---------- S3 ---------- #

variable "bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
}

# ---------- VPC ---------- #

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zone" {
  description = "The availability zone for the subnet"
  type        = string
  default     = "us-east-2a"
}
