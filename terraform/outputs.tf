output "prod_vpc_id" {
  value = aws_vpc.prod.id
}

output "prod_vpc_cidr_block" {
  value = aws_vpc.prod.cidr_block
}
output "internet_gateway_id" {
  value = aws_internet_gateway.prod.id
}

output "prod_public_route_table_id" {
  value = aws_route_table.prod_public.id
}

output "prod_public_subnet_ids" {
  value = aws_subnet.prod_public[*].id
}

output "prod_private_subnet_ids" {
  value = aws_subnet.prod_private[*].id
}

output "ichrisbirch_webserver_security_group_id" {
  value = aws_security_group.ichrisbirch_webserver.id
}

output "ichrisbirch_webserver_network_interface_id" {
  value = aws_network_interface.ichrisbirch_webserver.id
}

output "ichrisbirch_elastic_ip" {
  value = aws_eip.ichrisbirch_elastic_ip.public_ip
}

output "dynamodb_terraform_state_locking_table_id" {
  value = aws_dynamodb_table.ichrisbirch_terraform_state_locking.id
}

output "aws_ami_ichrisbirch_id" {
  value = data.aws_ami.ichrisbirch_t3medium_2vcpu_4gb_py312.id
}

output "aws_instance_ichrisbirch_webserver_id" {
  value = aws_instance.ichrisbirch_webserver.id
}

output "aws_instance_ichrisbirch_webserver_instance_type" {
  value = aws_instance.ichrisbirch_webserver.instance_type
}

output "aws_instance_ichrisbirch_webserver_iam_instance_profile" {
  value = aws_instance.ichrisbirch_webserver.iam_instance_profile
}

output "aws_instance_ichrisbirch_webserver_key_name" {
  value = aws_instance.ichrisbirch_webserver.key_name
}

output "aws_instance_ichrisbirch_webserver_subnet_id" {
  value = aws_instance.ichrisbirch_webserver.subnet_id
}

output "aws_instance_ichrisbirch_webserver_availability_zone" {
  value = aws_instance.ichrisbirch_webserver.availability_zone
}

output "aws_instance_ichrisbirch_webserver_security_groups" {
  value = aws_instance.ichrisbirch_webserver.security_groups
}

output "aws_db_instance_ichrisbirch_id" {
  value = aws_db_instance.ichrisbirch.id
}

output "aws_db_instance_ichrisbirch_endpoint" {
  value = aws_db_instance.ichrisbirch.endpoint
}

output "aws_db_instance_ichrisbirch_instance_class" {
  value = aws_db_instance.ichrisbirch.instance_class
}

output "aws_db_instance_ichrisbirch_engine" {
  value = aws_db_instance.ichrisbirch.engine
}

output "aws_db_instance_ichrisbirch_engine_version" {
  value = aws_db_instance.ichrisbirch.engine_version
}

output "aws_db_instance_ichrisbirch_security_group_ids" {
  value = aws_db_instance.ichrisbirch.vpc_security_group_ids
}
