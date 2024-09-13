# ---------- NETWORKING ---------- #

# VPC
# Subnets - Public and Private
# Internet Gateway
# Route Table
# Route Table Association
# Security Group
# Elastic IP
# Network Interface


resource "aws_vpc" "prod" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "Prod VPC"
  }
}

resource "aws_subnet" "prod_public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.prod.id
  cidr_block        = element(var.public_subnet_cidrs, count.index)
  availability_zone = element(local.azs, count.index)

  tags = {
    Name = "Prod Public Subnet ${count.index + 1}"
  }
}

resource "aws_subnet" "prod_private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.prod.id
  cidr_block        = element(var.private_subnet_cidrs, count.index)
  availability_zone = element(local.azs, count.index)

  tags = {
    Name = "Prod Private Subnet ${count.index + 1}"
  }
}

resource "aws_internet_gateway" "prod" {
  vpc_id = aws_vpc.prod.id

  tags = {
    Name = "Prod VPC Internet Gateway"
  }

}


resource "aws_route_table" "prod_public" {
  vpc_id = aws_vpc.prod.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.prod.id
  }

  tags = {
    Name = "Prod Public Route Table"
  }
}

resource "aws_route_table_association" "prod_public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = element(aws_subnet.prod_public[*].id, count.index)
  route_table_id = aws_route_table.prod_public.id
}




resource "aws_security_group" "ichrisbirch_webserver" {
  description = "HTTP, HTTPS, SSH"
  name        = "ichrisbirch-webserver"
  vpc_id      = aws_vpc.prod.id
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_out" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_http_ipv4_in" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_tls_ipv4_in" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_ssh_ipv4_in" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}


resource "aws_network_interface" "ichrisbirch_webserver" {
  subnet_id       = aws_subnet.prod_public[0].id
  security_groups = [aws_security_group.ichrisbirch_webserver.id]

  attachment {
    instance     = aws_instance.ichrisbirch_webserver.id
    device_index = 1
  }
}

resource "aws_eip" "ichrisbirch_elastic_ip" {
  domain            = "vpc"
  network_interface = aws_network_interface.ichrisbirch_webserver.id
  tags = {
    Name = "ichrisbirch.com"
  }
}









output "prod_id" {
  value = aws_vpc.prod.id
}

output "prod_cidr_block" {
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
