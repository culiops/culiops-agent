# BEFORE: aws_db_instance.main exists (being destroyed)
# AFTER: aws_rds_cluster.main + aws_rds_cluster_instance.main

resource "aws_rds_cluster" "main" {
  cluster_identifier = "userdb-${var.env}"
  engine             = "aurora-postgresql"
  engine_version     = "14.9"
  master_username    = var.db_username
  master_password    = var.db_password
  database_name      = "userdb"

  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = var.db_subnet_group

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  skip_final_snapshot     = false
  final_snapshot_identifier = "userdb-${var.env}-final-${formatdate("YYYYMMDD", timestamp())}"
}

resource "aws_rds_cluster_instance" "main" {
  identifier         = "userdb-${var.env}-instance-1"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  monitoring_role_arn = aws_iam_role.aurora_monitoring.arn
  monitoring_interval = 60
}

resource "aws_iam_role" "aurora_monitoring" {
  name = "userdb-${var.env}-aurora-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "aurora_monitoring" {
  role       = aws_iam_role.aurora_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_security_group" "db" {
  name_prefix = "userdb-${var.env}-"
  vpc_id      = var.vpc_id
}

resource "aws_security_group_rule" "db_ingress" {
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = var.app_subnet_cidrs
  security_group_id = aws_security_group.db.id
}
