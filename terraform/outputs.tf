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

output "webserver_ami_id" {
  value = data.aws_ami.ichrisbirch_t3medium_2vcpu_4gb_py312.id
}

output "webserver_availability_zone" {
  value = aws_instance.ichrisbirch_webserver.availability_zone
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

output "webserver_security_groups" {
  value = join(", ", aws_instance.ichrisbirch_webserver.vpc_security_group_ids[*])
}

output "webserver_subnet_id" {
  value = aws_instance.ichrisbirch_webserver.subnet_id
}

output "webserver_route_table_id" {
  value = aws_route_table.prod_public.id
}

output "webserver_elastic_ip" {
  value = aws_eip.ichrisbirch_elastic_ip.public_ip
}

output "network_interface_ichrisbirch_webserver_id" {
  value = aws_network_interface.ichrisbirch_webserver.id
}

output "security_group_ichrisbirch_webserver_id" {
  value = aws_security_group.ichrisbirch_webserver.id
}

output "internet_gateway_id" {
  value = aws_internet_gateway.prod.id
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
