# ---------- AWS ---------- #

provider "aws" {
  region = "us-east-1"
}

# ---------- DynamoDB ---------- #

resource "aws_dynamodb_table" "ichrisbirch-terraform-state-locking" {
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

data "aws_ami" "ichrisbirch" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "ichrisbirch_webserver" {
  ami                                  = data.aws_ami.ichrisbirch.id
  associate_public_ip_address          = "true"
  availability_zone                    = "us-east-1b"
  iam_instance_profile                 = "S3DatabaseBackups"
  instance_initiated_shutdown_behavior = "stop"
  instance_type                        = "t3.medium"
  ipv6_address_count                   = "0"
  key_name                             = "ichrisbirch-webserver"
  security_groups                      = [aws_security_group.ichrisbirch_webserver.name]
  vpc_security_group_ids               = [aws_security_group.ichrisbirch_webserver.id]
  subnet_id                            = aws_subnet.prod_public[0].id

  capacity_reservation_specification {
    capacity_reservation_preference = "open"
  }

  tags = {
    Name = "ichrisbirch"
  }

  tags_all = {
    Name = "ichrisbirch"
  }
}

# ---------- RDS ---------- #

resource "aws_db_instance" "ichrisbirch_pg16" {
  db_name             = "ichrisbirch-pg16"
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
