# ---------- Main Site ---------- #

resource "aws_route53_zone" "ichrisbirch_com" {
  comment       = "Main Site"
  force_destroy = false
  name          = "ichrisbirch.com"
}

resource "aws_route53_record" "www_ichrisbirch_com_a" {
  name    = "www.ichrisbirch.com"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
  ttl     = 300
  type    = "A"
  zone_id = aws_route53_zone.ichrisbirch_com.zone_id
}

resource "aws_route53_record" "docs_ichrisbirch_com_cname" {
  name    = "docs.ichrisbirch.com"
  records = ["datapointchris.github.io"]
  ttl     = 300
  type    = "CNAME"
  zone_id = aws_route53_zone.ichrisbirch_com.zone_id
}


# ---------- Docs Site ---------- #

resource "aws_route53_zone" "docs_ichrisbirch_com" {
  comment       = "Documentation Site"
  force_destroy = false
  name          = "docs.ichrisbirch.com"
}

resource "aws_route53_record" "docs_ichrisbirch_com_a" {
  name    = "docs.ichrisbirch.com"
  records = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
  ttl     = 300
  type    = "A"
  zone_id = aws_route53_zone.docs_ichrisbirch_com.zone_id
}


# ---------- API Subdomain ---------- #

resource "aws_route53_zone" "api_ichrisbirch_com" {
  comment       = "API Subdomain"
  force_destroy = false
  name          = "api.ichrisbirch.com"
}

resource "aws_route53_record" "api_ichrisbirch_com_a" {
  name    = "api.ichrisbirch.com"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
  ttl     = 300
  type    = "A"
  zone_id = aws_route53_zone.api_ichrisbirch_com.zone_id
}
