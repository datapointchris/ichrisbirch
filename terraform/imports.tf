# ----- DynamoDB Tables ----- #

import {
  to = aws_dynamodb_table.ichrisbirch_terraform_state_locking
  id = "ichrisbirch-terraform-state-locking"
}

# ----- S3 Buckets ----- #

import {
  to = aws_s3_bucket.ichrisbirch_backups
  id = "ichrisbirch-backups"
}

import {
  to = aws_s3_bucket.ichrisbirch_stats
  id = "ichrisbirch-stats"
}

import {
  to = aws_s3_bucket.ichrisbirch_terraform
  id = "ichrisbirch-terraform"
}

import {
  to = aws_s3_bucket.ichrisbirch_webserver_keys
  id = "ichrisbirch-webserver-keys"
}
