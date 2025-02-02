# Note: It is not necessary to create the `SOA` records
# as they are automatically created by AWS Route53
# and do not need to be referenced anywhere in the code.

# ---------- ichrisbirch.com / www.ichrisbirch.com ---------- #

resource "aws_route53_zone" "ichrisbirch" {
  name          = "ichrisbirch.com"
  comment       = "Main Site"
  force_destroy = false
}

resource "aws_route53_record" "ichrisbirch_a" {
  name    = "ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  ttl     = 300
  type    = "A"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
}

resource "aws_route53_record" "www_ichrisbirch_a" {
  name    = "www.ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  ttl     = 300
  type    = "A"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
}

resource "aws_route53_record" "ichrisbirch_ns" {
  name            = "ichrisbirch.com"
  zone_id         = aws_route53_zone.ichrisbirch.zone_id
  ttl             = 172800
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.ichrisbirch.name_servers
}

resource "aws_route53_record" "api_ichrisbirch_ns_ns" {
  name            = "api.ichrisbirch.com"
  zone_id         = aws_route53_zone.ichrisbirch.zone_id
  ttl             = 300
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.api_ichrisbirch.name_servers
  depends_on      = [aws_route53_zone.api_ichrisbirch]
}

resource "aws_route53_record" "chat_ichrisbirch_ns_ns" {
  name            = "chat.ichrisbirch.com"
  zone_id         = aws_route53_zone.ichrisbirch.zone_id
  ttl             = 300
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.chat_ichrisbirch.name_servers
  depends_on      = [aws_route53_zone.chat_ichrisbirch]
}

resource "aws_route53_record" "docs_ichrisbirch_cname" {
  name    = "docs.ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  ttl     = 300
  type    = "CNAME"
  records = ["datapointchris.github.io"]
}


# ---------- api.ichrisbirch.com ---------- #

resource "aws_route53_zone" "api_ichrisbirch" {
  name          = "api.ichrisbirch.com"
  comment       = "API Subdomain"
  force_destroy = false
}

resource "aws_route53_record" "api_ichrisbirch_a" {
  name    = "api.ichrisbirch.com"
  zone_id = aws_route53_zone.api_ichrisbirch.zone_id
  ttl     = 300
  type    = "A"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
}


resource "aws_route53_record" "api_ichrisbirch_ns" {
  name            = "api.ichrisbirch.com"
  zone_id         = aws_route53_zone.api_ichrisbirch.zone_id
  ttl             = 172800
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.api_ichrisbirch.name_servers
}


# ---------- chat.ichrisbirch.com ---------- #

resource "aws_route53_zone" "chat_ichrisbirch" {
  name          = "chat.ichrisbirch.com"
  comment       = "API Subdomain"
  force_destroy = false
}

resource "aws_route53_record" "chat_ichrisbirch_a" {
  name    = "chat.ichrisbirch.com"
  zone_id = aws_route53_zone.chat_ichrisbirch.zone_id
  ttl     = 300
  type    = "A"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
}


resource "aws_route53_record" "chat_ichrisbirch_ns" {
  name            = "chat.ichrisbirch.com"
  zone_id         = aws_route53_zone.chat_ichrisbirch.zone_id
  ttl             = 172800
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.chat_ichrisbirch.name_servers
}


# ---------- docs.ichrisbirch.com ---------- #

resource "aws_route53_zone" "docs_ichrisbirch" {
  name          = "docs.ichrisbirch.com"
  comment       = "Documentation Site"
  force_destroy = false
}

resource "aws_route53_record" "docs_ichrisbirch_a" {
  name    = "docs.ichrisbirch.com"
  zone_id = aws_route53_zone.docs_ichrisbirch.zone_id
  ttl     = 300
  type    = "A"
  records = [
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153"
  ]
}

resource "aws_route53_record" "docs_ichrisbirch_ns" {
  name            = "docs.ichrisbirch.com"
  zone_id         = aws_route53_zone.docs_ichrisbirch.zone_id
  ttl             = 172800
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.docs_ichrisbirch.name_servers
}
