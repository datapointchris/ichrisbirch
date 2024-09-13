# ---------- AWS ---------- #

provider "aws" {
  region = "us-east-2"
}

# ---------- DynamoDB ---------- #

resource "aws_dynamodb_table" "ichrisbirch_terraform_state_locking" {
  name                        = "ichrisbirch-terraform-state-locking"
  hash_key                    = "LockID"
  billing_mode                = "PROVISIONED"
  deletion_protection_enabled = "false"
  read_capacity               = "1"
  stream_enabled              = "false"
  table_class                 = "STANDARD"
  write_capacity              = "1"

  attribute {
    name = "LockID"
    type = "S"
  }
  point_in_time_recovery {
    enabled = "false"
  }
}

# ---------- EC2 ---------- #

data "aws_ami" "ichrisbirch_t3medium_2vcpu_4gb_py312" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["ichrisbirch-t3medium-2vcpu-4gb-py312"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = data.aws_availability_zones.available.names
}

resource "aws_instance" "ichrisbirch_webserver" {
  ami = data.aws_ami.ichrisbirch_t3medium_2vcpu_4gb_py312.id
  # ami                                  = "ami-085f9c64a9b75eed5" # Ubuntu 24.04
  associate_public_ip_address = true
  availability_zone           = local.azs[0]
  iam_instance_profile        = aws_iam_instance_profile.ichrisbirch_webserver.name
  instance_type               = "t3.medium"
  key_name                    = "ichrisbirch-webserver"
  security_groups             = [aws_security_group.ichrisbirch_webserver.id]
  subnet_id                   = element(aws_subnet.prod_public, 0).id

  instance_market_options {
    market_type = "spot"
  }

  tags = {
    Name = "ichrisbirch"
  }
  depends_on = [aws_security_group.ichrisbirch_webserver]
}

# ---------- RDS ---------- #

resource "aws_db_instance" "ichrisbirch_pg16" {
  identifier          = "ichrisbirch-pg16"
  instance_class      = "db.t3.micro"
  engine              = "postgres"
  engine_version      = "16.2"
  allocated_storage   = 20
  skip_final_snapshot = true
  username            = var.db_username
  password            = var.db_password
}

# ---------- S3 ---------- #

resource "aws_s3_bucket" "ichrisbirch_backups" {
  bucket = "ichrisbirch-backups"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ichrisbirch_backups" {
  bucket = aws_s3_bucket.ichrisbirch_backups.bucket

  rule {
    id     = "Delete after 30 days"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_backups" {
  bucket = aws_s3_bucket.ichrisbirch_backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "ichrisbirch_stats" {
  bucket = "ichrisbirch-stats"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_stats" {
  bucket = aws_s3_bucket.ichrisbirch_stats.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "ichrisbirch_terraform" {
  bucket = "ichrisbirch-terraform"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_terraform" {
  bucket = aws_s3_bucket.ichrisbirch_terraform.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "ichrisbirch_webserver_keys" {
  bucket = "ichrisbirch-webserver-keys"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_webserver_keys" {
  bucket = aws_s3_bucket.ichrisbirch_webserver_keys.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "ichrisbirch_webserver_keys_admin_role_only_policy" {
  bucket = aws_s3_bucket.ichrisbirch_webserver_keys.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.admin.arn
        }
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.ichrisbirch_webserver_keys.arn,
          format("%s/*", aws_s3_bucket.ichrisbirch_webserver_keys.arn),
        ]
      }
    ]
  })
}
