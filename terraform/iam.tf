data "aws_caller_identity" "current" {}


resource "aws_iam_instance_profile" "S3DatabaseBackups" {
  name = "S3DatabaseBackups"
  path = "/"
  role = "S3DatabaseBackups"
}

# ---------- ROLES ---------- #

resource "aws_iam_policy" "AllowPassRoleS3DatabaseBackups" {
  name        = "AllowPassRoleS3DatabaseBackups"
  description = "Allow Get and Pass Role for S3DatabaseBackups Role"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "iam:PassRole",
          "iam:GetRole"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:iam::215933706506:role/S3DatabaseBackups"
      }
    ]
  })
}

resource "aws_iam_role" "S3DatabaseBackups" {
  name        = "S3DatabaseBackups"
  description = "Allows EC2 instances to call AWS services on your behalf."
  managed_policy_arns = [
    aws_iam_policy.AllowPassRoleS3DatabaseBackups.arn,
    "arn:aws:iam::215933706506:policy/AWSKeyManagementServiceUser",
    "arn:aws:iam::aws:policy/AmazonRDSFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  ]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "export.rds.amazonaws.com"
        }
      }
    ]
  })


}


resource "aws_iam_role_policy_attachment" "S3DatabaseBackups_AWSKeyManagementServiceUser" {
  policy_arn = "arn:aws:iam::215933706506:policy/AWSKeyManagementServiceUser"
  role       = "S3DatabaseBackups"
}

resource "aws_iam_role_policy_attachment" "S3DatabaseBackups_AllowPassRoleS3DatabaseBackups" {
  policy_arn = "arn:aws:iam::215933706506:policy/AllowPassRoleS3DatabaseBackups"
  role       = "S3DatabaseBackups"
}

resource "aws_iam_role_policy_attachment" "S3DatabaseBackups_AmazonRDSFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
  role       = "S3DatabaseBackups"
}

resource "aws_iam_role_policy_attachment" "S3DatabaseBackups_AmazonS3FullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = "S3DatabaseBackups"
}


resource "aws_iam_role" "admin_role" {
  name = "AdminRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/chris.birch"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "admin_role_policy_attachment" {
  role       = aws_iam_role.admin_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_policy" "assume_admin_role_policy" {
  name        = "AssumeAdminRolePolicy"
  description = "Policy to allow assuming the admin role"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = aws_iam_role.admin_role.arn
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "developer_user_policy_attachment" {
  user       = "developer_user"
  policy_arn = aws_iam_policy.assume_admin_role_policy.arn
}

# ---------- USER GROUPS ---------- #

resource "aws_iam_group" "admin" {
  name = "admin"
}

resource "aws_iam_group" "developer" {
  name = "developer"
}

# ---------- USER GROUP POLICIES ---------- #

resource "aws_iam_group_policy_attachment" "admin_AdministratorAccess" {
  group      = "admin"
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AWSLambda_FullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AmazonDynamoDBFullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AmazonEC2FullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AmazonECS_FullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AmazonRDSFullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AmazonS3FullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_group_policy_attachment" "developer_AmazonSSMFullAccess" {
  group      = "developer"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}

# ---------- USERS ---------- #

resource "aws_iam_user" "chris_birch_developer" {
  name = "chris.birch.developer"
}

resource "aws_iam_user" "john_kundycki" {
  name = "john.kundycki"
}

resource "aws_iam_user" "chris_birch_admin" {
  name = "chris.birch.admin"
}

# ---------- USER GROUP MEMBERSHIPS ---------- #

resource "aws_iam_user_group_membership" "chris_birch_admin_admin" {
  groups = ["admin"]
  user   = "chris.birch.admin"
}

resource "aws_iam_user_group_membership" "chris_birch_developer-002F-developer" {
  groups = ["developer"]
  user   = "chris.birch.developer"
}

resource "aws_iam_user_group_membership" "john-002E-kundycki-002F-admin" {
  groups = ["admin"]
  user   = "john.kundycki"
}

# ---------- USER POLICIES ---------- #

resource "aws_iam_user_policy_attachment" "chris_birch_admin_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "chris.birch.admin"
}

resource "aws_iam_user_policy_attachment" "chris_birch_developer_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "chris.birch.developer"
}

resource "aws_iam_user_policy_attachment" "john_kundycki_IAMUserChangePassword" {
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"
  user       = "john.kundycki"
}

# ---------- USER ACCESS KEYS ---------- #

resource "aws_iam_access_key" "chris_birch_admin" {
  depends_on = [aws_iam_user.chris_birch_admin]
  status     = "Active"
  user       = "chris.birch.admin"
}

resource "aws_iam_access_key" "chris_birch_developer" {
  depends_on = [aws_iam_user.chris_birch_developer]
  status     = "Active"
  user       = "chris.birch.developer"
}


output "aws_iam_role_S3DatabaseBackups_id" {
  value = aws_iam_role.S3DatabaseBackups.id
}
