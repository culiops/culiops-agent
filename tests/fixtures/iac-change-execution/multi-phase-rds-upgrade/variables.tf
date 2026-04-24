variable "env" {
  description = "Environment name (e.g. prod, staging)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the database is deployed"
  type        = string
}

variable "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  type        = string
}

variable "app_security_group_id" {
  description = "Security group ID of the application tier (ECS tasks)"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "db_storage_gb" {
  description = "Initial allocated storage in GB"
  type        = number
}

variable "db_max_storage_gb" {
  description = "Maximum allocated storage for autoscaling (GB)"
  type        = number
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarm notifications"
  type        = string
}
