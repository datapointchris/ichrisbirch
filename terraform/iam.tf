# -------------------- DATA SOURCES -------------------- #

data "aws_caller_identity" "current" {}

data "tls_certificate" "github_actions" {
  url = var.gh_actions_token_url
}

data "aws_iam_policy" "admin" {
  arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

data "aws_iam_policy" "billing" {
  arn = "arn:aws:iam::aws:policy/job-function/Billing"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions = ["sts:AssumeRole"]
  }
}


# -------------------- IDENTITY PROVIDERS -------------------- #

resource "aws_iam_openid_connect_provider" "github" {
  url            = data.tls_certificate.github_actions.url
  client_id_list = ["sts.amazonaws.com"]
  # thumbprint_list = ["a031c46782e6e6c662c2c87c76da9aa62ccabd8e"]
  thumbprint_list = data.tls_certificate.github_actions.certificates[*].sha1_fingerprint
}


# -------------------- ROLES -------------------- #

resource "aws_iam_role" "github_actions" {
  name = "GithubActions${title(var.gh_org)}${title(var.gh_repo)}Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
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
  name = "WebserverRole"

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

resource "aws_iam_role" "terraform" {
  name               = "TerraformRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role" "admin" {
  name               = "AdminRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}


# -------------------- ASSUME ROLE POLICIES -------------------- #

resource "aws_iam_policy" "assume_admin_role" {
  name        = "AssumeAdmin"
  description = "Policy to allow assuming the admin role"
  depends_on  = [aws_iam_role.admin]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = aws_iam_role.admin.arn
      }
    ]
  })
}

resource "aws_iam_policy" "assume_terraform_role" {
  name        = "AssumeTerraform"
  description = "Policy to allow assuming the terraform role"
  depends_on  = [aws_iam_role.terraform]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = aws_iam_role.terraform.arn
      }
    ]
  })
}

# -------------------- POLICIES -------------------- #

resource "aws_iam_policy" "terraform_execution" {
  name        = "TerraformExecution"
  description = "Policy to allow Terraform to execute changes in the AWS account"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:*",
          "dynamodb:*",
          "ec2:*",
          "ecs:*",
          "rds:*",
          "route53:*",
          "s3:*",
          "ssm:*",
          "iam:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "access_webserver_keys" {
  name        = "AccessWebserverKeys"
  description = "Policy to allow access to the webserver keys"

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

resource "aws_iam_policy" "ec2_instance_connect" {
  name        = "EC2InstanceConnect"
  description = "Policy to allow EC2 Instance Connect"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ec2-instance-connect:SendSSHPublicKey"
        Resource = "arn:aws:ec2:*:*:instance/*"
      }
    ]
  })
}

resource "aws_iam_policy" "allow_pass_webserver_role" {
  name        = "AllowPassRoleToWebserverRole"
  description = "Policy to allow passing the WebserverRole"

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

resource "aws_iam_policy" "cloud_developer" {
  name        = "CloudDeveloper"
  description = "Combined policy for general cloud development"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "lambda:*",
          "dynamodb:*",
          "ec2:*",
          "ecs:*",
          "rds:*",
          "route53:*",
          "s3:*",
          "ssm:*"
        ],
        Resource = "*"
      }
    ]
  })
}


# -------------------- ROLE POLICY ATTACHMENTS -------------------- #

resource "aws_iam_role_policy_attachment" "github_actions_terraform_execution" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.terraform_execution.arn
}

resource "aws_iam_role_policy_attachment" "terraform_role_terraform_execution" {
  role       = aws_iam_role.terraform.name
  policy_arn = aws_iam_policy.terraform_execution.arn
}

resource "aws_iam_role_policy_attachment" "webserver_access_webserver_keys" {
  role       = aws_iam_role.ichrisbirch_webserver.name
  policy_arn = aws_iam_policy.access_webserver_keys.arn
}

# --- Admin --- #
resource "aws_iam_role_policy_attachment" "admin_access_webserver_keys" {
  role       = aws_iam_role.admin.name
  policy_arn = aws_iam_policy.access_webserver_keys.arn
}

resource "aws_iam_role_policy_attachment" "admin_administrator_access" {
  role       = aws_iam_role.admin.name
  policy_arn = data.aws_iam_policy.admin.arn
}

resource "aws_iam_role_policy_attachment" "admin_view_cost_and_usage" {
  role       = aws_iam_role.admin.name
  policy_arn = data.aws_iam_policy.billing.arn
}


# -------------------- INSTANCE PROFILES -------------------- #

resource "aws_iam_instance_profile" "ichrisbirch_webserver" {
  name = "WebserverInstanceProfile"
  role = aws_iam_role.ichrisbirch_webserver.name
}


# -------------------- USERS -------------------- #

resource "aws_iam_user" "chris_birch" {
  name = "chris.birch"
}

resource "aws_iam_user_login_profile" "chris_birch" {
  user                    = aws_iam_user.chris_birch.name
  password_reset_required = true
}

resource "aws_iam_user" "john_kundycki" {
  name = "john.kundycki"
}


# -------------------- USER POLICIES -------------------- #

resource "aws_iam_user_policy_attachment" "chris_birch_iam_user_change_password" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "chris.birch"
}

resource "aws_iam_user_policy_attachment" "john_kundycki_iam_user_change_password" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "john.kundycki"
}


# -------------------- USER GROUPS -------------------- #

resource "aws_iam_group" "developer" {
  name = "developer"
}

resource "aws_iam_group" "developer_admin" {
  name = "developer-admin"
}

resource "aws_iam_group" "security" {
  name = "security"
}


# -------------------- USER GROUP POLICY ATTACHMENTS -------------------- #

# --- Developer --- #

resource "aws_iam_group_policy_attachment" "developer_ec2_instance_connect" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.ec2_instance_connect.arn
}

resource "aws_iam_group_policy_attachment" "developer_pass_webserver_role" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.allow_pass_webserver_role.arn
}

resource "aws_iam_group_policy_attachment" "developer_cloud_developer" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.cloud_developer.arn
}

# --- Developer Admin --- #

resource "aws_iam_group_policy_attachment" "developer_admin_assume_admin" {
  group      = aws_iam_group.developer_admin.name
  policy_arn = aws_iam_policy.assume_admin_role.arn
}

resource "aws_iam_group_policy_attachment" "developer_admin_assume_terraform" {
  group      = aws_iam_group.developer_admin.name
  policy_arn = aws_iam_policy.assume_terraform_role.arn
}

# --- Security --- #

resource "aws_iam_group_policy_attachment" "security_assume_adming" {
  group      = aws_iam_group.security.name
  policy_arn = aws_iam_policy.assume_admin_role.arn
}

# -------------------- GROUP MEMBERSHIPS -------------------- #

resource "aws_iam_group_membership" "developer" {
  name  = "developer"
  group = aws_iam_group.developer.name
  users = [aws_iam_user.chris_birch.name, aws_iam_user.john_kundycki.name]
}

resource "aws_iam_group_membership" "developer_admin" {
  name  = "developer-admin"
  group = aws_iam_group.developer_admin.name
  users = [aws_iam_user.chris_birch.name]
}
