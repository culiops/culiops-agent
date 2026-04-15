output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}

output "public_subnet_ids" {
  value = module.vpc.public_subnets
}

output "db_primary_endpoint" {
  value = aws_db_instance.primary.endpoint
}

output "db_replica_endpoint" {
  value = aws_db_instance.replica.endpoint
}

output "db_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the DB master password."
  value       = aws_db_instance.primary.master_user_secret[0].secret_arn
}

output "cache_primary_endpoint" {
  value = aws_elasticache_replication_group.cache.primary_endpoint_address
}

output "cache_reader_endpoint" {
  value = aws_elasticache_replication_group.cache.reader_endpoint_address
}

output "uploads_bucket_name" {
  value = aws_s3_bucket.uploads.id
}

output "uploads_bucket_arn" {
  value = aws_s3_bucket.uploads.arn
}

output "async_queue_url" {
  value = aws_sqs_queue.async.url
}

output "async_queue_arn" {
  value = aws_sqs_queue.async.arn
}

output "async_dlq_arn" {
  value = aws_sqs_queue.async_dlq.arn
}
