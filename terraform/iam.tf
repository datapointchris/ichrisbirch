
# ---------- ROLES ---------- #

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

resource "aws_iam_role" "admin" {
  name       = "AdminRole"
  depends_on = [aws_iam_user.chris_birch]

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_user.chris_birch.arn
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}


# ---------- POLICIES ---------- #

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

resource "aws_iam_policy" "assume_admin_role" {
  name        = "AssumeAdminRole"
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

# ---------- ROLE POLICY ATTACHMENTS ---------- #

resource "aws_iam_role_policy_attachment" "webserver_access_webserver_keys" {
  role       = aws_iam_role.ichrisbirch_webserver.name
  policy_arn = aws_iam_policy.access_webserver_keys.arn
}

resource "aws_iam_role_policy_attachment" "admin_access_webserver_keys" {
  role       = aws_iam_role.admin.name
  policy_arn = aws_iam_policy.access_webserver_keys.arn
}

resource "aws_iam_role_policy_attachment" "admin_administrator_access" {
  role       = aws_iam_role.admin.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_role_policy_attachment" "admin_view_cost_and_usage" {
  role       = aws_iam_role.admin.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/Billing"
}


# ---------- INSTANCE PROFILES ---------- #

resource "aws_iam_instance_profile" "ichrisbirch_webserver" {
  name = "WebserverInstanceProfile"
  role = aws_iam_role.ichrisbirch_webserver.name
}


# ---------- USER GROUPS ---------- #

resource "aws_iam_group" "developer" {
  name = "developer"
}


# ---------- USER GROUP POLICIES ---------- #

resource "aws_iam_group_policy_attachment" "developer_ec2_instance_connect" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.ec2_instance_connect.arn
}

resource "aws_iam_group_policy_attachment" "developer_pass_webserver_role" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.allow_pass_webserver_role.arn
}

resource "aws_iam_group_policy_attachment" "developer_assume_admin_role" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.assume_admin_role.arn
}

resource "aws_iam_group_policy_attachment" "developer_cloud_developer" {
  group      = aws_iam_group.developer.name
  policy_arn = aws_iam_policy.cloud_developer.arn
}


# ---------- USERS ---------- #

resource "aws_iam_user" "chris_birch" {
  name       = "chris.birch"
  depends_on = [aws_iam_group.developer]
}

resource "aws_iam_user_login_profile" "chris_birch" {
  user                    = aws_iam_user.chris_birch.name
  password_reset_required = true
}

resource "aws_iam_user" "john_kundycki" {
  name       = "john.kundycki"
  depends_on = [aws_iam_group.developer]
}


# ---------- USER GROUP MEMBERSHIPS ---------- #

resource "aws_iam_user_group_membership" "chris_birch_developer" {
  groups = ["developer"]
  user   = "chris.birch"
}

resource "aws_iam_user_group_membership" "john_kundycki_developer" {
  groups = ["developer"]
  user   = "john.kundycki"
}


# ---------- USER POLICIES ---------- #

resource "aws_iam_user_policy_attachment" "chris_birch_iam_user_change_password" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "chris.birch"
}

resource "aws_iam_user_policy_attachment" "john_kundycki_iam_user_change_password" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "john.kundycki"
}
