variable "env" {
  description = "Environment name"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic for alarm notifications"
  type        = string
}
