# --- ACCOUNT ESTATE, READ BY NAME ---------------------------------------- #
# The account's users, groups, roles and OIDC provider are administered outside this repo.

data "aws_caller_identity" "current" {}

data "aws_iam_openid_connect_provider" "github" {
  url = var.gh_actions_token_url
}

data "aws_iam_role" "admin" {
  name = "AdminRole"
}

data "aws_iam_group" "developer" {
  group_name = "developer"
}

data "aws_iam_policy" "terraform_execution" {
  name = "terraform-execution"
}

data "aws_iam_policy" "assume_terraform_role" {
  name = "assume-terraform"
}

data "aws_iam_policy" "deny_dynamodb_autoscaling" {
  name = "deny-dynamodb-autoscaling"
}


# --- ROLES ---------------------------------------- #

resource "aws_iam_role" "github_actions" {
  name = "github-actions-${var.gh_repo}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.gh_org}/${var.gh_repo}:*"
          }
        }
      }
    ]
  })
}

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

resource "aws_iam_role_policy_attachment" "github_actions_terraform_execution" {
  role       = aws_iam_role.github_actions.name
  policy_arn = data.aws_iam_policy.terraform_execution.arn
}

resource "aws_iam_role_policy_attachment" "github_actions_assume_terraform_role" {
  role       = aws_iam_role.github_actions.name
  policy_arn = data.aws_iam_policy.assume_terraform_role.arn
}

resource "aws_iam_role_policy_attachment" "github_actions_deny_dynamodb_autoscaling" {
  role       = aws_iam_role.github_actions.name
  policy_arn = data.aws_iam_policy.deny_dynamodb_autoscaling.arn
}

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
