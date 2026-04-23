output "db_endpoint" {
  value       = aws_rds_cluster.main.endpoint
  description = "Aurora cluster writer endpoint — consumed by userapi, authapi, billingapi"
}

output "db_reader_endpoint" {
  value       = aws_rds_cluster.main.reader_endpoint
  description = "Aurora cluster reader endpoint"
}

output "db_port" {
  value = 5432
}
