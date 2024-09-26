# ---------- NETWORKING ---------- #

# VPC
# Internet Gateway
# Public Subnet
# Public Route Table
# Public Route Table Association
# Public Route Table Main Association
# Private Subnet
# Private Route Table
# Private Route Table Association
# Security Group
# # Egress Allow All Traffic Out
# # Ingress Allow All HTTP IPv4 In
# # Ingress Allow All TLS IPv4 In
# # Ingress Allow All SSH IPv4 In
# # Ingress Allow All ICMP IPv4 In
# # Ingress Allow Postgres Inside SG
# Network Interface
# Elastic IP
# Elastic IP Association

data "aws_availability_zones" "available" { state = "available" }

# VPC
resource "aws_vpc" "prod" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "Prod VPC" }
}

# Internet Gateway
resource "aws_internet_gateway" "prod" {
  vpc_id = aws_vpc.prod.id
  tags   = { Name = "Prod VPC Internet Gateway" }
}


# --- PUBLIC ---------------------------------------- #

# Public Subnet
resource "aws_subnet" "prod_public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.prod.id
  cidr_block        = element(var.public_subnet_cidrs, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)
  tags              = { Name = "Prod Public Subnet ${count.index + 1}" }
}

# Public Route Table
resource "aws_route_table" "prod_public" {
  vpc_id = aws_vpc.prod.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.prod.id
  }
  tags = { Name = "Prod Public Route Table" }
}

# Public Route Table Association
resource "aws_route_table_association" "prod_public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = element(aws_subnet.prod_public[*].id, count.index)
  route_table_id = aws_route_table.prod_public.id
}

# Public Route Table Main Association
resource "aws_main_route_table_association" "prod_public" {
  vpc_id         = aws_vpc.prod.id
  route_table_id = aws_route_table.prod_public.id
}


# --- PRIVATE ---------------------------------------- #

# Private Subnet
resource "aws_subnet" "prod_private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.prod.id
  cidr_block        = element(var.private_subnet_cidrs, count.index)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)
  tags              = { Name = "Prod Private Subnet ${count.index + 1}" }
}

# Private Route Table
resource "aws_route_table" "prod_private" {
  vpc_id = aws_vpc.prod.id
  tags   = { Name = "Prod Private Route Table" }
}

# Private Route Table Association
resource "aws_route_table_association" "prod_private" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = element(aws_subnet.prod_private[*].id, count.index)
  route_table_id = aws_route_table.prod_private.id
}


# --- SECURITY GROUPS ---------------------------------------- #

# --- Webserver --- #

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
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_tls_ipv4_in" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_ssh_ipv4_in" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "allow_all_icmp_ipv4_in" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "icmp"
  from_port         = -1
  to_port           = -1
  /* ICMP (Internet Control Message Protocol) traffic consists of network layer
    messages used for diagnostic and control purposes.
    Unlike protocols such as TCP and UDP, ICMP doesn't carry application data.
    Instead, it facilitates communication about the status of the network itself.
    ping and traceback
  */
}


# --- Database --- #

resource "aws_security_group" "ichrisbirch_database" {
  description = "Postgres"
  name        = "ichrisbirch-database"
  vpc_id      = aws_vpc.prod.id
}

resource "aws_vpc_security_group_ingress_rule" "allow_postgres_from_webserver" {
  security_group_id            = aws_security_group.ichrisbirch_database.id
  referenced_security_group_id = aws_security_group.ichrisbirch_webserver.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "postgres_out_all_vpc" {
  security_group_id = aws_security_group.ichrisbirch_webserver.id
  cidr_ipv4         = aws_vpc.prod.cidr_block
  ip_protocol       = "tcp"
  from_port         = 5432
  to_port           = 5432
}


# --- NETWORK INTERFACES ---------------------------------------- #

# Network Interface
resource "aws_network_interface" "ichrisbirch_webserver" {
  subnet_id       = element(aws_subnet.prod_public, 0).id
  security_groups = [aws_security_group.ichrisbirch_webserver.id]
  tags            = { Name = "ichrisbirch-webserver-eni" }
}

# Elastic IP
resource "aws_eip" "ichrisbirch_elastic_ip" {
  domain = "vpc"
  tags   = { Name = "ichrisbirch.com" }
}

# Elastic IP Association
resource "aws_eip_association" "ichrisbirch_elastic_ip_assoc" {
  allocation_id        = aws_eip.ichrisbirch_elastic_ip.id
  network_interface_id = aws_network_interface.ichrisbirch_webserver.id
}
