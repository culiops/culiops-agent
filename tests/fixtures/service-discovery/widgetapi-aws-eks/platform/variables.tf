variable "environment" {
  description = "Deployment environment (prod, staging)."
  type        = string
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "eu-west-1"
}

variable "eks_version" {
  description = "EKS control-plane version."
  type        = string
  default     = "1.29"
}

variable "node_instance_types" {
  description = "Instance types for the default node group."
  type        = list(string)
}

variable "node_min_size" {
  description = "Minimum node count."
  type        = number
}

variable "node_max_size" {
  description = "Maximum node count."
  type        = number
}

variable "node_desired_size" {
  description = "Desired node count."
  type        = number
}
