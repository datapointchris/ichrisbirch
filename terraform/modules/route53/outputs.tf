output "domain_name" {
  description = "The domain name in Route 53"
  value       = aws_route53_zone.main.name
}
