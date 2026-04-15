variable "environment" {
  description = "Deployment environment (prod, staging)."
  type        = string
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "eu-west-1"
}

variable "vpc_cidr" {
  description = "Primary CIDR for the VPC."
  type        = string
}

variable "availability_zones" {
  description = "AZs to stretch subnets across."
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs (one per AZ)."
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs (one per AZ)."
  type        = list(string)
}

variable "single_nat_gateway" {
  description = "If true, use one NAT gateway for all AZs (cheaper, less HA)."
  type        = bool
  default     = false
}

variable "db_instance_class" {
  description = "RDS primary instance class."
  type        = string
}

variable "db_replica_instance_class" {
  description = "RDS read-replica instance class."
  type        = string
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GB."
  type        = number
}

variable "db_max_allocated_storage" {
  description = "Upper bound for storage autoscaling."
  type        = number
}

variable "db_multi_az" {
  description = "Whether the primary is multi-AZ."
  type        = bool
}

variable "db_backup_retention_days" {
  description = "RDS backup retention window in days."
  type        = number
}

variable "cache_node_type" {
  description = "ElastiCache node type."
  type        = string
}

variable "cache_num_nodes" {
  description = "Number of cache clusters in the replication group."
  type        = number
}

variable "queue_visibility_timeout" {
  description = "SQS visibility timeout in seconds for the async queue."
  type        = number
  default     = 60
}
