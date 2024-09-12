# ---------- Main Site ---------- #

resource "aws_route53_zone" "ichrisbirch_com" {
  comment       = "Main Site"
  force_destroy = false
  name          = "ichrisbirch.com"
}

resource "aws_route53_record" "www_ichrisbirch_com_A" {
  name = "www.ichrisbirch.com"
  # records                          = ["23.22.30.103"]
  records = [aws_eip.ichrisbirch_elastic_ip.public_ip]
  ttl     = 300
  type    = "A"
  zone_id = aws_route53_zone.ichrisbirch_com.zone_id
}

resource "aws_route53_record" "ichrisbirch_com_NS" {
  name    = "ichrisbirch.com"
  records = ["ns-1342.awsdns-39.org.", "ns-1734.awsdns-24.co.uk.", "ns-226.awsdns-28.com.", "ns-721.awsdns-26.net."]
  ttl     = 172800
  type    = "NS"
  zone_id = aws_route53_zone.ichrisbirch_com.zone_id
}

resource "aws_route53_record" "ichrisbirch_com_SOA" {
  name    = "ichrisbirch.com"
  records = ["ns-721.awsdns-26.net. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
  ttl     = 900
  type    = "SOA"
  zone_id = aws_route53_zone.ichrisbirch_com.zone_id
}



# ---------- Docs Site ---------- #

resource "aws_route53_zone" "docs_ichrisbirch_com" {
  comment       = "Documentation Site"
  force_destroy = false
  name          = "docs.ichrisbirch.com"
}

resource "aws_route53_record" "docs_ichrisbirch_com_A" {
  name    = "docs.ichrisbirch.com"
  records = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
  ttl     = 300
  type    = "A"
  zone_id = aws_route53_zone.docs_ichrisbirch_com.zone_id
}

resource "aws_route53_record" "docs_ichrisbirch_com_NS" {
  name    = "docs.ichrisbirch.com"
  records = ["ns-1191.awsdns-20.org.", "ns-1708.awsdns-21.co.uk.", "ns-323.awsdns-40.com.", "ns-749.awsdns-29.net."]
  ttl     = 172800
  type    = "NS"
  zone_id = aws_route53_zone.docs_ichrisbirch_com.zone_id
}

resource "aws_route53_record" "docs_ichrisbirch_com_SOA" {
  name    = "docs.ichrisbirch.com"
  records = ["ns-749.awsdns-29.net. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
  ttl     = 900
  type    = "SOA"
  zone_id = aws_route53_zone.docs_ichrisbirch_com.zone_id
}

resource "aws_route53_record" "docs_ichrisbirch_com_CNAME" {
  name    = "docs.ichrisbirch.com"
  records = ["datapointchris.github.io"]
  ttl     = 300
  type    = "CNAME"
  zone_id = aws_route53_zone.docs_ichrisbirch_com.zone_id
}

# ---------- API Subdomain ---------- #





resource "aws_route53_zone" "api_ichrisbirch_com" {
  comment       = "API Subdomain"
  force_destroy = false
  name          = "api.ichrisbirch.com"
}




resource "aws_route53_record" "api_ichrisbirch_com_A" {
  name    = "api.ichrisbirch.com"
  records = ["23.22.30.103"]
  ttl     = 300
  type    = "A"
  zone_id = aws_route53_zone.api_ichrisbirch_com.zone_id
}

resource "aws_route53_record" "api_ichrisbirch_com_NS" {
  name    = "api.ichrisbirch.com"
  records = ["ns-115.awsdns-14.com.", "ns-1275.awsdns-31.org.", "ns-1639.awsdns-12.co.uk.", "ns-804.awsdns-36.net."]
  ttl     = 172800
  type    = "NS"
  zone_id = aws_route53_zone.api_ichrisbirch_com.zone_id
}

resource "aws_route53_record" "api_ichrisbirch_com_SOA" {
  name    = "api.ichrisbirch.com"
  records = ["ns-115.awsdns-14.com. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
  ttl     = 900
  type    = "SOA"
  zone_id = aws_route53_zone.api_ichrisbirch_com.zone_id
}
