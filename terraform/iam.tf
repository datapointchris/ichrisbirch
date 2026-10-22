# --- ACCOUNT ESTATE, READ BY NAME ---------------------------------------- #
# The account's users, groups and roles are administered outside this repo. terraform-role, which
# applies this root, may change only the IAM declared below, so a new role or policy here also needs
# terraform-execution's allowance widened where that policy is declared.

data "aws_caller_identity" "current" {}

data "aws_iam_role" "admin" {
  name = "AdminRole"
}

data "aws_iam_group" "developer" {
  group_name = "developer"
}


# --- ROLES ---------------------------------------- #

resource "aws_iam_role" "ichrisbirch_webserver" {
  name = "webserver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}


# --- POLICIES ---------------------------------------- #

resource "aws_iam_policy" "access_webserver_keys" {
  name        = "access-webserver-keys"
  description = "Allow access to the webserver keys"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
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

resource "aws_iam_policy" "access_backups_bucket" {
  name        = "access-backups-bucket"
  description = "Allow access to the ichrisbirch backups bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.ichrisbirch_backups.arn,
          format("%s/*", aws_s3_bucket.ichrisbirch_backups.arn),
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "allow_pass_webserver_role" {
  name        = "allow-pass-webserver-role"
  description = "Allow passing the WebserverRole"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.ichrisbirch_webserver.arn
      }
    ]
  })
}


# --- ROLE POLICY ATTACHMENTS ---------------------------------------- #

resource "aws_iam_role_policy_attachment" "webserver_access_webserver_keys" {
  role       = aws_iam_role.ichrisbirch_webserver.name
  policy_arn = aws_iam_policy.access_webserver_keys.arn
}

resource "aws_iam_role_policy_attachment" "webserver_access_backups_bucket" {
  role       = aws_iam_role.ichrisbirch_webserver.name
  policy_arn = aws_iam_policy.access_backups_bucket.arn
}


# --- INSTANCE PROFILES ---------------------------------------- #

resource "aws_iam_instance_profile" "ichrisbirch_webserver" {
  name = "webserver-instance-profile"
  role = aws_iam_role.ichrisbirch_webserver.name
}


# --- GROUP POLICY ATTACHMENTS ---------------------------------------- #

resource "aws_iam_group_policy_attachment" "developer_pass_webserver_role" {
  group      = data.aws_iam_group.developer.group_name
  policy_arn = aws_iam_policy.allow_pass_webserver_role.arn
}
