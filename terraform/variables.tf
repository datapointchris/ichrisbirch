# ---------- Route 53 ---------- #

variable "domain_name" {
  description = "The domain name for Route 53"
  type        = string
}

# ---------- S3 ---------- #

variable "bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
}

# ---------- VPC ---------- #

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zone" {
  description = "The availability zone for the subnet"
  type        = string
  default     = "us-east-2a"
}
