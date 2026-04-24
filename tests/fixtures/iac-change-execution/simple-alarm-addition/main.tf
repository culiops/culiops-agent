# paymentapi — ECS Fargate service, ap-southeast-1
# This file represents the EXISTING state of the infrastructure.
# The CloudWatch CPU alarm is intentionally absent — it is what
# the iac-change-execution skill would be asked to add.

# ── ECS cluster ──────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "paymentapi" {
  name = "paymentapi-cluster-${var.env}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

# ── Task definition ───────────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "paymentapi" {
  family                   = "paymentapi-${var.env}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "paymentapi"
      image     = "${var.ecr_repo}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "APP_ENV", value = var.env },
        { name = "DB_HOST", value = var.db_host },
        { name = "PORT",    value = "8080" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/paymentapi-${var.env}"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

# ── ECS service ───────────────────────────────────────────────────────────────

resource "aws_ecs_service" "paymentapi" {
  name            = "paymentapi-svc-${var.env}"
  cluster         = aws_ecs_cluster.paymentapi.id
  task_definition = aws_ecs_task_definition.paymentapi.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.paymentapi.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.paymentapi.arn
    container_name   = "paymentapi"
    container_port   = 8080
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

# ── Security group ────────────────────────────────────────────────────────────

resource "aws_security_group" "paymentapi" {
  name_prefix = "paymentapi-${var.env}-"
  vpc_id      = var.vpc_id
  description = "paymentapi ${var.env} task security group"

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
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

# ── ALB target group ──────────────────────────────────────────────────────────

resource "aws_lb_target_group" "paymentapi" {
  name        = "paymentapi-tg-${var.env}"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/healthz"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

# ── CloudWatch log group ──────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "paymentapi" {
  name              = "/ecs/paymentapi-${var.env}"
  retention_in_days = 30

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}

# ── SNS topic (alerts) ────────────────────────────────────────────────────────

resource "aws_sns_topic" "paymentapi_alerts" {
  name = "paymentapi-alerts-${var.env}"

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}
