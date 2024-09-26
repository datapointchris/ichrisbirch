# ------------------------------------------------------------------ #
# AWS
# ------------------------------------------------------------------ #

output "aws_region" {
  value = var.region
}

output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "aws_caller_identity_arn" {
  value = data.aws_caller_identity.current.arn
}

# ------------------------------------------------------------------ #
# DATABASE
# ------------------------------------------------------------------ #

output "db_endpoint" {
  value = aws_db_instance.icb.endpoint
}

output "db_engine" {
  value = aws_db_instance.icb.engine
}

output "db_engine_version" {
  value = aws_db_instance.icb.engine_version
}

output "db_id" {
  value = aws_db_instance.icb.id
}

output "db_instance_class" {
  value = aws_db_instance.icb.instance_class
}

output "db_security_group_ids" {
  value = join(", ", aws_db_instance.icb.vpc_security_group_ids[*])
}

output "dynamodb_terraform_state_locking_table_id" {
  value = aws_dynamodb_table.ichrisbirch_terraform_state_locking.id
}

# ------------------------------------------------------------------ #
# NETWORK
# ------------------------------------------------------------------ #

output "internet_gateway_id" {
  value = aws_internet_gateway.prod.id
}

output "network_interface_ichrisbirch_webserver_id" {
  value = aws_network_interface.ichrisbirch_webserver.id
}

output "prod_private_route_table_id" {
  value = aws_route_table.prod_private.id
}

output "prod_private_subnet_ids" {
  value = join(", ", aws_subnet.prod_private[*].id)
}

output "prod_public_route_table_id" {
  value = aws_route_table.prod_public.id
}

output "prod_public_subnet_ids" {
  value = join(", ", aws_subnet.prod_public[*].id)
}

output "prod_vpc_cidr_block" {
  value = aws_vpc.prod.cidr_block
}

output "prod_vpc_id" {
  value = aws_vpc.prod.id
}

output "security_group_ichrisbirch_webserver_id" {
  value = aws_security_group.ichrisbirch_webserver.id
}

# ------------------------------------------------------------------ #
# WEBSERVER
# ------------------------------------------------------------------ #

output "webserver_ami_id" {
  value = data.aws_ami.ichrisbirch_webserver.id
}

output "webserver_availability_zone" {
  value = aws_instance.ichrisbirch_webserver.availability_zone
}

output "webserver_elastic_ip" {
  value = aws_eip.ichrisbirch_elastic_ip.public_ip
}

output "webserver_iam_instance_profile" {
  value = aws_instance.ichrisbirch_webserver.iam_instance_profile
}

output "webserver_id" {
  value = aws_instance.ichrisbirch_webserver.id
}

output "webserver_instance_type" {
  value = aws_instance.ichrisbirch_webserver.instance_type
}

output "webserver_key_name" {
  value = aws_instance.ichrisbirch_webserver.key_name
}

output "webserver_route_table_id" {
  value = aws_route_table.prod_public.id
}

output "webserver_security_groups" {
  value = join(", ", aws_instance.ichrisbirch_webserver.vpc_security_group_ids[*])
}

output "webserver_subnet_id" {
  value = aws_instance.ichrisbirch_webserver.subnet_id
}

# ------------------------------------------------------------------ #
# IAM
# ------------------------------------------------------------------ #

# ---------- IDENTITY PROVIDERS ---------- #

output "iam_oidc_provider_github_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}

# ---------- ROLES ---------- #

output "iam_role_github_actions_arn" {
  value = aws_iam_role.github_actions.arn
}

output "iam_role_terraform_arn" {
  value = aws_iam_role.terraform.arn
}

output "iam_role_ichrisbirch_webserver_arn" {
  value = aws_iam_role.ichrisbirch_webserver.arn
}

output "iam_role_admin_arn" {
  value = aws_iam_role.admin.arn
}


# ---------- ASSUME ROLE POLICIES ---------- #

output "iam_policy_assume_admin_role_arn" {
  value = aws_iam_policy.assume_admin_role.arn
}

output "iam_policy_assume_terraform_role_arn" {
  value = aws_iam_policy.assume_terraform_role.arn
}

# ---------- POLICIES ---------- #

output "iam_policy_terraform_execution_arn" {
  value = aws_iam_policy.terraform_execution.arn
}

output "iam_policy_access_webserver_keys_arn" {
  value = aws_iam_policy.access_webserver_keys.arn
}

output "iam_policy_ec2_instance_connect_arn" {
  value = aws_iam_policy.ec2_instance_connect.arn
}

output "iam_policy_allow_pass_webserver_role_arn" {
  value = aws_iam_policy.allow_pass_webserver_role.arn
}

output "iam_policy_cloud_developer_arn" {
  value = aws_iam_policy.cloud_developer.arn
}


# ---------- IAM INSTANCE PROFILES ---------- #

output "iam_instance_profile_ichrisbirch_webserver_arn" {
  value = aws_iam_instance_profile.ichrisbirch_webserver.arn
}

# ---------- IAM GROUPS ---------- #

output "iam_group_developer_arn" {
  value = aws_iam_group.developer.arn
}

output "iam_group_developer_admin_arn" {
  value = aws_iam_group.developer_admin.arn
}

output "iam_group_security_arn" {
  value = aws_iam_group.security.arn
}

# ---------- IAM USERS ---------- #

output "iam_user_chris_birch_arn" {
  value = aws_iam_user.chris_birch.arn
}

output "iam_user_john_kundycki_arn" {
  value = aws_iam_user.john_kundycki.arn
}

output "user_chris_birch_generated_password" {
  value     = aws_iam_user_login_profile.chris_birch.password
  sensitive = true
}

# ------------------------------------------------------------------ #
# ROUTE 53
# ------------------------------------------------------------------ #

# ---------- Main Site ---------- #

output "route53_ichrisbirch_zone_name" {
  value = aws_route53_zone.ichrisbirch.name
}

output "route53_ichrisbirch_zone_id" {
  value = aws_route53_zone.ichrisbirch.zone_id
}

output "route53_ichrisbirch_zone_name_servers" {
  value = join(", ", aws_route53_zone.ichrisbirch.name_servers[*])
}

output "route53_ichrisbirch_zone_primary_name_server" {
  value = aws_route53_zone.ichrisbirch.primary_name_server
}

# ---------- API Subdomain ---------- #

output "route53_api_ichrisbirch_zone_name" {
  value = aws_route53_zone.api_ichrisbirch.name
}

output "route53_api_ichrisbirch_zone_id" {
  value = aws_route53_zone.api_ichrisbirch.zone_id
}

output "route53_api_ichrisbirch_zone_name_servers" {
  value = join(", ", aws_route53_zone.api_ichrisbirch.name_servers[*])
}

output "route53_api_ichrisbirch_zone_primary_name_server" {
  value = aws_route53_zone.api_ichrisbirch.primary_name_server
}

# ---------- Docs Site ---------- #

output "route53_docs_ichrisbirch_zone_name" {
  value = aws_route53_zone.docs_ichrisbirch.name
}

output "route53_docs_ichrisbirch_zone_id" {
  value = aws_route53_zone.docs_ichrisbirch.zone_id
}

output "route53_docs_ichrisbirch_zone_name_servers" {
  value = join(", ", aws_route53_zone.docs_ichrisbirch.name_servers[*])
}

output "route53_docs_ichrisbirch_zone_primary_name_server" {
  value = aws_route53_zone.docs_ichrisbirch.primary_name_server
}
