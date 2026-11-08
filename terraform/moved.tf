# Each block maps a resource's earlier address to its current one, so state follows the
# address without replacing the resource. The AWS-side names are set in the resources themselves.

moved {
  from = aws_security_group.ichrisbirch_webserver
  to   = aws_security_group.life_webserver
}

moved {
  from = aws_security_group.ichrisbirch_database
  to   = aws_security_group.life_database
}

moved {
  from = aws_db_subnet_group.icb
  to   = aws_db_subnet_group.life
}

moved {
  from = aws_s3_bucket.ichrisbirch_backups
  to   = aws_s3_bucket.life_backups
}

moved {
  from = aws_s3_bucket_lifecycle_configuration.ichrisbirch_backups
  to   = aws_s3_bucket_lifecycle_configuration.life_backups
}

moved {
  from = aws_s3_bucket_public_access_block.ichrisbirch_backups
  to   = aws_s3_bucket_public_access_block.life_backups
}

moved {
  from = aws_s3_bucket.ichrisbirch_stats
  to   = aws_s3_bucket.life_stats
}

moved {
  from = aws_s3_bucket_public_access_block.ichrisbirch_stats
  to   = aws_s3_bucket_public_access_block.life_stats
}

moved {
  from = aws_s3_bucket.ichrisbirch_webserver_keys
  to   = aws_s3_bucket.life_webserver_keys
}

moved {
  from = aws_s3_bucket_public_access_block.ichrisbirch_webserver_keys
  to   = aws_s3_bucket_public_access_block.life_webserver_keys
}

moved {
  from = aws_s3_bucket_policy.ichrisbirch_webserver_keys_admin_role_only_policy
  to   = aws_s3_bucket_policy.life_webserver_keys_admin_role_only_policy
}

moved {
  from = aws_iam_role.ichrisbirch_webserver
  to   = aws_iam_role.life_webserver
}

moved {
  from = aws_iam_instance_profile.ichrisbirch_webserver
  to   = aws_iam_instance_profile.life_webserver
}
