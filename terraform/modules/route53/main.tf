resource "aws_route53_zone" "main" {
  name = var.domain_name
}

output "domain_name" {
  value = aws_route53_zone.main.name
}
