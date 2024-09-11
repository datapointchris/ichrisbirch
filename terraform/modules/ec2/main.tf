resource "aws_instance" "this" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  security_groups = [aws_security_group.this.name]
}

output "instance_id" {
  value = aws_instance.main.id
}
