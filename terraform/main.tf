# --- DynamoDB ---------------------------------------- #

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


# --- EC2 ---------------------------------------- #

# data "aws_ami" "ichrisbirch_webserver" {
#   most_recent = true
#   owners      = ["self"]
#
#   filter {
#     name   = "name"
#     values = ["ichrisbirch-t3medium-2vcpu-4gb-py312"]
#   }
# }
#
# resource "aws_instance" "ichrisbirch_webserver" {
#   # Cannot use the following properties when attaching a network interface:
#   #   subnet_id
#   #   vpc_security_group_ids
#   #   associate_public_ip_address
#   ami                  = data.aws_ami.ichrisbirch_webserver.id
#   availability_zone    = data.aws_availability_zones.available.names[0]
#   iam_instance_profile = aws_iam_instance_profile.ichrisbirch_webserver.name
#   instance_type        = "t3.medium"
#   key_name             = "ichrisbirch-webserver"
#   tags                 = { Name = "ichrisbirch_webserver" }
#   depends_on           = [aws_security_group.ichrisbirch_webserver, aws_network_interface.ichrisbirch_webserver]
#
#   # The network interface must be attached here when the instance is created in order
#   # to have it be the primary network interface that the elastic IP can be associated with.
#   # If it is secondary, SSH and inbound traffic will not work.
#   # https://repost.aws/knowledge-center/ec2-ubuntu-secondary-network-interface
#   network_interface {
#     device_index         = 0
#     network_interface_id = aws_network_interface.ichrisbirch_webserver.id
#   }
#
#   # instance_market_options {
#   #   market_type = "spot"
#   # }
# }


# --- RDS ---------------------------------------- #

resource "aws_db_subnet_group" "icb" {
  name       = "icb"
  subnet_ids = [element(aws_subnet.prod_private, 0).id, element(aws_subnet.prod_private, 1).id, element(aws_subnet.prod_private, 2).id]
}

# resource "aws_db_instance" "icb" {
#   identifier = "icb-db"
#   # do not create the database because the pg_restore command will do that
#   # db_name             = "ichrisbirch" # name of the database to create
#   instance_class      = "db.t3.micro"
#   engine              = "postgres"
#   engine_version      = "16.3"
#   allocated_storage   = 20
#   skip_final_snapshot = true
#   # snapshot_identifier    = aws_db_snapshot.db_snapshot.id
#   username               = var.db_username
#   password               = var.db_password
#   publicly_accessible    = false
#   db_subnet_group_name   = aws_db_subnet_group.icb.name
#   vpc_security_group_ids = [aws_security_group.ichrisbirch_database.id]
#   depends_on             = [aws_security_group.ichrisbirch_database]
# }


# --- S3 ---------------------------------------- #

resource "aws_s3_bucket" "ichrisbirch_backups" {
  bucket = "ichrisbirch-backups"
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_lifecycle_configuration" "ichrisbirch_backups" {
  bucket = aws_s3_bucket.ichrisbirch_backups.bucket
  rule {
    id     = "Delete after 30 days"
    status = "Enabled"
    expiration { days = 30 }
  }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_backups" {
  bucket                  = aws_s3_bucket.ichrisbirch_backups.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "ichrisbirch_stats" {
  bucket = "ichrisbirch-stats"
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_stats" {
  bucket                  = aws_s3_bucket.ichrisbirch_stats.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "ichrisbirch_terraform" {
  bucket = "ichrisbirch-terraform"
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_terraform" {
  bucket                  = aws_s3_bucket.ichrisbirch_terraform.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "ichrisbirch_webserver_keys" {
  bucket = "ichrisbirch-webserver-keys"
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_public_access_block" "ichrisbirch_webserver_keys" {
  bucket                  = aws_s3_bucket.ichrisbirch_webserver_keys.id
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
