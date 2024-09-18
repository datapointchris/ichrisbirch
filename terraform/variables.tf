# ---------- AWS ---------- #

variable "region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-2"
}


# ---------- GITHUB ---------- #

variable "gh_org" {
  description = "Name of the Github Organization."
  type        = string
  default     = "datapointchris"
}

variable "gh_repo" {
  description = "Name of the ECR Repository- should match the Github repo name."
  type        = string
  default     = "ichrisbirch"
}

variable "gh_actions_token_url" {
  description = "URL for the Github Actions API"
  type        = string
  default     = "https://token.actions.githubusercontent.com"
}


# ---------- RDS ---------- #

variable "db_username" {
  description = "The username for the database"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "The password for the database"
  type        = string
  sensitive   = true
}


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
