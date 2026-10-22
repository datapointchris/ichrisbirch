# ---------- AWS ---------- #

variable "account_id" {
  description = "The account this applies into, where the provider assumes terraform-role. docs/terraform.md sets it from the credentials in use."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id must be exactly 12 digits."
  }
}

variable "region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-2"
}


# ---------- RDS ---------- #

# variable "db_username" {
#   description = "The username for the database"
#   type        = string
#   sensitive   = true
# }
#
# variable "db_password" {
#   description = "The password for the database"
#   type        = string
#   sensitive   = true
# }


# ---------- VPC ---------- #

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "Public Subnet CIDR values"
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "Private Subnet CIDR values"
  default     = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
}
