# Project Configuration
project_name = "revolut-birthday-api"
environment  = "dev"

# AWS Configuration
aws_region = "eu-central-1"

# Network Configuration
vpc_cidr        = "10.0.0.0/16"
public_subnets  = ["10.0.1.0/24","10.0.2.0/24"]
private_subnets = ["10.0.10.0/24","10.0.20.0/24"]

# Application Configuration
app_port        = 8001
app_count       = 2
fargate_cpu     = 256
fargate_memory  = 512

# Domain Configuration
domain_name = "revolut-api.com"

# DynamoDB Configuration
dynamodb_table_name   = "users_birthdays"
dynamodb_table_prefix = "users_"

# IAM Configuration
iam_role_name = "revolut-birthday-api-role"
