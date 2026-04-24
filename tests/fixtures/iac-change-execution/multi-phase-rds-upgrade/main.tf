# paymentapi — RDS PostgreSQL 15 database, ap-southeast-1
# This file represents the EXISTING state of the infrastructure.
# max_connections is currently 100; the skill will be asked to raise it to 200
# and reboot the instance.

# ── RDS parameter group ───────────────────────────────────────────────────────

resource "aws_db_parameter_group" "paymentapi" {
  name_prefix = "paymentapi-${var.env}-"
  family      = "postgres15"
  description = "paymentapi ${var.env} PostgreSQL 15 parameter group"

  parameter {
    name  = "max_connections"
    value = "100"
  }

  parameter {
    name         = "log_min_duration_statement"
    value        = "1000"
    apply_method = "immediate"
  }

  parameter {
    name         = "log_checkpoints"
    value        = "1"
    apply_method = "immediate"
  }

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── RDS instance ──────────────────────────────────────────────────────────────

resource "aws_db_instance" "paymentapi" {
  identifier = "paymentapi-db-${var.env}"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_storage_gb
  max_allocated_storage = var.db_max_storage_gb
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "paymentapi"
  username = "paymentapi_admin"
  password = var.db_password

  parameter_group_name   = aws_db_parameter_group.paymentapi.name
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = [aws_security_group.paymentapi_db.id]

  multi_az               = var.env == "prod" ? true : false
  backup_retention_period = 7
  backup_window          = "17:00-18:00"
  maintenance_window     = "Mon:18:00-Mon:19:00"

  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "paymentapi-db-${var.env}-final"

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

# ── Security group (DB) ───────────────────────────────────────────────────────

resource "aws_security_group" "paymentapi_db" {
  name_prefix = "paymentapi-db-${var.env}-"
  vpc_id      = var.vpc_id
  description = "paymentapi ${var.env} database security group"

  ingress {
    description     = "PostgreSQL from app tier"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── CloudWatch alarms ─────────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "paymentapi_db_cpu" {
  alarm_name          = "paymentapi-db-cpu-high-${var.env}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization above 80% for paymentapi ${var.env}"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.paymentapi.identifier
  }

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

resource "aws_cloudwatch_metric_alarm" "paymentapi_db_connections" {
  alarm_name          = "paymentapi-db-connections-high-${var.env}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS connections above 80 for paymentapi ${var.env} (limit: 100)"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.paymentapi.identifier
  }

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}
