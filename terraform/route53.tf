
# ---------- Main Site ---------- #

resource "aws_route53_zone" "ichrisbirch" {
  name          = "ichrisbirch.com"
  comment       = "Main Site"
  force_destroy = false
}

resource "aws_route53_record" "www_ichrisbirch_a" {
  name    = "www.ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  # ttl     = 300
  ttl     = 30
  type    = "A"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
}

# resource "aws_route53_record" "ichrisbirch_soa" {
#   name    = "ichrisbirch.com"
#   zone_id = aws_route53_zone.ichrisbirch.zone_id
#   # ttl             = 900
#   ttl             = 30
#   type            = "SOA"
#   allow_overwrite = true
#   records         = ["ns-721.awsdns-26.net. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
# }

resource "aws_route53_record" "ichrisbirch_ns" {
  name    = "ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  # ttl             = 172800
  ttl             = 30
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.ichrisbirch.name_servers
}

resource "aws_route53_record" "api_ichrisbirch_ns_ns" {
  name    = "api.ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  # ttl             = 300
  ttl             = 30
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.api_ichrisbirch.name_servers
  depends_on      = [aws_route53_zone.api_ichrisbirch]
}


# ---------- API Subdomain ---------- #

resource "aws_route53_zone" "api_ichrisbirch" {
  name          = "api.ichrisbirch.com"
  comment       = "API Subdomain"
  force_destroy = false
}

resource "aws_route53_record" "api_ichrisbirch_a" {
  name    = "api.ichrisbirch.com"
  zone_id = aws_route53_zone.api_ichrisbirch.zone_id
  # ttl     = 300
  ttl     = 30
  type    = "A"
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
}

# resource "aws_route53_record" "api_ichrisbirch_soa" {
#   name    = "api.ichrisbirch.com"
#   zone_id = aws_route53_zone.api_ichrisbirch.zone_id
#   # ttl             = 900
#   ttl             = 30
#   type            = "SOA"
#   allow_overwrite = true
#   records         = ["ns-115.awsdns-14.com. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
# }

resource "aws_route53_record" "api_ichrisbirch_ns" {
  name    = "api.ichrisbirch.com"
  zone_id = aws_route53_zone.api_ichrisbirch.zone_id
  # ttl             = 172800
  ttl             = 30
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.api_ichrisbirch.name_servers
}




# ---------- Docs Site ---------- #

resource "aws_route53_zone" "docs_ichrisbirch" {
  name          = "docs.ichrisbirch.com"
  comment       = "Documentation Site"
  force_destroy = false
}

resource "aws_route53_record" "docs_ichrisbirch_a" {
  name    = "docs.ichrisbirch.com"
  zone_id = aws_route53_zone.docs_ichrisbirch.zone_id
  # ttl     = 300
  ttl  = 30
  type = "A"
  records = [
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153"
  ]
}

# resource "aws_route53_record" "docs_ichrisbirch_soa" {
#   name    = "docs.ichrisbirch.com"
#   zone_id = aws_route53_zone.docs_ichrisbirch.zone_id
#   # ttl             = 900
#   ttl             = 30
#   type            = "SOA"
#   allow_overwrite = true
#   records         = ["ns-749.awsdns-29.net. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
# }

resource "aws_route53_record" "docs_ichrisbirch_ns" {
  name    = "docs.ichrisbirch.com"
  zone_id = aws_route53_zone.docs_ichrisbirch.zone_id
  # ttl             = 172800
  ttl             = 30
  type            = "NS"
  allow_overwrite = true
  records         = aws_route53_zone.docs_ichrisbirch.name_servers
}

resource "aws_route53_record" "docs_ichrisbirch_cname" {
  name    = "docs.ichrisbirch.com"
  zone_id = aws_route53_zone.ichrisbirch.zone_id
  # ttl     = 300
  ttl     = 30
  type    = "CNAME"
  records = ["datapointchris.github.io"]
}
