# ------------------------------------------------------------------ #
# DATABASE
# ------------------------------------------------------------------ #

output "db_endpoint" {
  value = aws_db_instance.ichrisbirch.endpoint
}

output "db_engine" {
  value = aws_db_instance.ichrisbirch.engine
}

output "db_engine_version" {
  value = aws_db_instance.ichrisbirch.engine_version
}

output "db_id" {
  value = aws_db_instance.ichrisbirch.id
}

output "db_instance_class" {
  value = aws_db_instance.ichrisbirch.instance_class
}

output "db_security_group_ids" {
  value = join(", ", aws_db_instance.ichrisbirch.vpc_security_group_ids[*])
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
  value = aws_subnet.prod_private[*].id
}

output "prod_public_route_table_id" {
  value = aws_route_table.prod_public.id
}

output "prod_public_subnet_ids" {
  value = aws_subnet.prod_public[*].id
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
  value = data.aws_ami.ichrisbirch_t3medium_2vcpu_4gb_py312.id
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

# ---------- IAM ROLES ---------- #

output "iam_role_admin_arn" {
  value = aws_iam_role.admin.arn
}

output "iam_role_admin_name" {
  value = aws_iam_role.admin.name
}

output "iam_role_ichrisbirch_webserver_arn" {
  value = aws_iam_role.ichrisbirch_webserver.arn
}

output "iam_role_ichrisbirch_webserver_name" {
  value = aws_iam_role.ichrisbirch_webserver.name
}

# ---------- IAM POLICIES ---------- #

output "iam_policy_access_webserver_keys_arn" {
  value = aws_iam_policy.access_webserver_keys.arn
}

output "iam_policy_access_webserver_keys_name" {
  value = aws_iam_policy.access_webserver_keys.name
}

output "iam_policy_allow_pass_webserver_role_arn" {
  value = aws_iam_policy.allow_pass_webserver_role.arn
}

output "iam_policy_allow_pass_webserver_role_name" {
  value = aws_iam_policy.allow_pass_webserver_role.name
}

output "iam_policy_assume_admin_role_arn" {
  value = aws_iam_policy.assume_admin_role.arn
}

output "iam_policy_assume_admin_role_name" {
  value = aws_iam_policy.assume_admin_role.name
}

output "iam_policy_cloud_developer_arn" {
  value = aws_iam_policy.cloud_developer.arn
}

output "iam_policy_cloud_developer_name" {
  value = aws_iam_policy.cloud_developer.name
}

output "iam_policy_ec2_instance_connect_arn" {
  value = aws_iam_policy.ec2_instance_connect.arn
}

output "iam_policy_ec2_instance_connect_name" {
  value = aws_iam_policy.ec2_instance_connect.name
}

# ---------- IAM INSTANCE PROFILES ---------- #

output "iam_instance_profile_ichrisbirch_webserver_arn" {
  value = aws_iam_instance_profile.ichrisbirch_webserver.arn
}

output "iam_instance_profile_ichrisbirch_webserver_name" {
  value = aws_iam_instance_profile.ichrisbirch_webserver.name
}

# ---------- IAM GROUPS ---------- #

output "iam_group_developer_arn" {
  value = aws_iam_group.developer.arn
}

output "iam_group_developer_name" {
  value = aws_iam_group.developer.name
}

# ---------- IAM USERS ---------- #

output "iam_user_chris_birch_arn" {
  value = aws_iam_user.chris_birch.arn
}

output "iam_user_chris_birch_name" {
  value = aws_iam_user.chris_birch.name
}

output "iam_user_john_kundycki_arn" {
  value = aws_iam_user.john_kundycki.arn
}

output "iam_user_john_kundycki_name" {
  value = aws_iam_user.john_kundycki.name
}

output "user_chris_birch_generated_password" {
  value     = aws_iam_user_login_profile.chris_birch.password
  sensitive = true
}

# ------------------------------------------------------------------ #
# ROUTE 53
# ------------------------------------------------------------------ #

# ---------- Main Site ---------- #

output "route53_api_ichrisbirch_ns_ns_fqdn" {
  value = aws_route53_record.api_ichrisbirch_ns_ns.fqdn
}

output "route53_api_ichrisbirch_ns_ns_name" {
  value = aws_route53_record.api_ichrisbirch_ns_ns.name
}

output "route53_ichrisbirch_ns_fqdn" {
  value = aws_route53_record.ichrisbirch_ns.fqdn
}

output "route53_ichrisbirch_ns_name" {
  value = aws_route53_record.ichrisbirch_ns.name
}

output "route53_ichrisbirch_zone_id" {
  value = aws_route53_zone.ichrisbirch.zone_id
}

output "route53_ichrisbirch_zone_name_servers" {
  value = aws_route53_zone.ichrisbirch.name_servers
}

output "route53_ichrisbirch_zone_primary_name_server" {
  value = aws_route53_zone.ichrisbirch.primary_name_server
}

output "route53_www_ichrisbirch_a_fqdn" {
  value = aws_route53_record.www_ichrisbirch_a.fqdn
}

output "route53_www_ichrisbirch_a_name" {
  value = aws_route53_record.www_ichrisbirch_a.name
}

# ---------- API Subdomain ---------- #

output "route53_api_ichrisbirch_a_fqdn" {
  value = aws_route53_record.api_ichrisbirch_a.fqdn
}

output "route53_api_ichrisbirch_a_name" {
  value = aws_route53_record.api_ichrisbirch_a.name
}

output "route53_api_ichrisbirch_ns_fqdn" {
  value = aws_route53_record.api_ichrisbirch_ns.fqdn
}

output "route53_api_ichrisbirch_ns_name" {
  value = aws_route53_record.api_ichrisbirch_ns.name
}

output "route53_api_ichrisbirch_zone_id" {
  value = aws_route53_zone.api_ichrisbirch.zone_id
}

output "route53_api_ichrisbirch_zone_name_servers" {
  value = aws_route53_zone.api_ichrisbirch.name_servers
}

output "route53_api_ichrisbirch_zone_primary_name_server" {
  value = aws_route53_zone.api_ichrisbirch.primary_name_server
}

# ---------- Docs Site ---------- #

output "route53_docs_ichrisbirch_zone_id" {
  value = aws_route53_zone.docs_ichrisbirch.zone_id
}

output "route53_docs_ichrisbirch_zone_name_servers" {
  value = aws_route53_zone.docs_ichrisbirch.name_servers
}

output "route53_docs_ichrisbirch_zone_primary_name_server" {
  value = aws_route53_zone.docs_ichrisbirch.primary_name_server
}

output "route53_docs_ichrisbirch_ns_name" {
  value = aws_route53_record.docs_ichrisbirch_ns.name
}

output "route53_docs_ichrisbirch_ns_fqdn" {
  value = aws_route53_record.docs_ichrisbirch_ns.fqdn
}

output "route53_docs_ichrisbirch_a_name" {
  value = aws_route53_record.docs_ichrisbirch_a.name
}

output "route53_docs_ichrisbirch_a_fqdn" {
  value = aws_route53_record.docs_ichrisbirch_a.fqdn
}

output "route53_docs_ichrisbirch_cname_name" {
  value = aws_route53_record.docs_ichrisbirch_cname.name
}

output "route53_docs_ichrisbirch_cname_fqdn" {
  value = aws_route53_record.docs_ichrisbirch_cname.fqdn
}
