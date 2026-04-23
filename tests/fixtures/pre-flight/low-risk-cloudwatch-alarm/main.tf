resource "aws_cloudwatch_metric_alarm" "orderapi_cpu" {
  alarm_name          = "orderapi-${var.env}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU utilization above 80% for orderapi ${var.env}"

  dimensions = {
    ClusterName = "orderapi-cluster-${var.env}"
    ServiceName = "orderapi-svc-${var.env}"
  }

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]
}
