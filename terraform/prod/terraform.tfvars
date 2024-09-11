# ---------- AWS ---------- #

region             = "us-east-2"

# ---------- DynamoDB ---------- #

terraform_state_table_name   = "ichrisbirch-terraform-state"
terraform_state_hash_key     = "userID"
terraform_state_hash_key_type = "S"

# ---------- EC2 ---------- #

instance_type      = "t3.medium"
ami_id             = "ami-12345678"
security_group_id  = "sg-12345678"

# ---------- RDS ---------- #

db_instance_class  = "db.t2.micro"
db_name            = "dev_db"
db_username        = "dev_user"
db_password        = "dev_password"

# ---------- VPC ---------- #

vpc_cidr           = "10.0.0.0/16"
