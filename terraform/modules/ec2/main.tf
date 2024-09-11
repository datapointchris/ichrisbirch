resource "aws_instance" "this" {
  ami           = var.ichrisbirch_ami_id
  instance_type = var.ichrisbirch_instance_type
  subnet_id     = var.ichrisbirch_subnet_id
}

output "instance_id" {
  value = aws_instance.main.id
}
