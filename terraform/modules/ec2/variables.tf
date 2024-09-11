variable "ichrisbirch_instance_type" {
  description = "The type of instance to use"
  type        = string
}

variable "ichrisbirch_ami_id" {
  description = "The AMI ID to use for the instance"
  type        = string
}

variable "ichrisbirch_subnet_id" {
  description = "The subnet ID to deploy the instance into"
  type        = string
}
