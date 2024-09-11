# ---------- AWS ---------- #

provider "aws" {
  region = "us-east-1"
}

# ---------- DynamoDB ---------- #

resource "aws_dynamodb_table" "ichrisbirch-terraform-state" {
  name         = "ichrisbirch-terraform-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userID"

  attribute {
    name = this.hash_key
    type = "S"
  }
}

# ---------- EC2 ---------- #

resource "aws_instance" "ichrisbirch-webserver" {
  instance_type   = "t3.medium"
  ami            = "ami-0c55b159cbfafe1f0"
  security_groups = [aws_security_group.this.name]
  subnet_id      = module.vpc.subnet_id
}


# ---------- IAM ---------- #

# module "iam" {
#   source = "../modules/iam"
# }



# ---------- RDS ---------- #

resource "rds" "ichrisbirch-pg16" {
  db_name           = "ichrisbirch-pg16"
  db_instance_class = "db.t3.micro"
  db_username       = var.db_username
  db_password       = var.db_password
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.subnet_ids
}

# ---------- Route 53 ---------- #

# module "route53" {
#   source      = "../modules/route53"
#   domain_name = var.domain_name
# }

# ---------- S3 ---------- #

variable "bucket_names" {
  type    = list(string)
  default = ["ichrisbirch-backups", "ichrisbirch-stats", "ichrisbirch-terraform"]
}

resource "aws_s3_bucket" "buckets" {
  for_each = toset(var.bucket_names)

  bucket = each.value

  lifecycle {
    prevent_destroy = true
  }
}

# ---------- VPC ---------- #

# module "vpc" {
#   source   = "../modules/vpc"
#   vpc_cidr = var.vpc_cidr
# }
