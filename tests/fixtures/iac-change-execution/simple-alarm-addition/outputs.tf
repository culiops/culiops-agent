output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.paymentapi.name
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.paymentapi.name
}

output "target_group_arn" {
  description = "ALB target group ARN"
  value       = aws_lb_target_group.paymentapi.arn
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.paymentapi_alerts.arn
}
