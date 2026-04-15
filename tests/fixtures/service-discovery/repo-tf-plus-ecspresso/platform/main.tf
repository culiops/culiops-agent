terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "orderapi-tfstate"
    key    = "platform/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region
}

resource "aws_ecs_cluster" "main" {
  name = "orderapi-${var.env}"
}

resource "aws_lb" "main" {
  name               = "orderapi-${var.env}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.public_subnets
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "orderapi" {
  name        = "orderapi-${var.env}-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
}

resource "aws_security_group" "alb" {
  name   = "orderapi-${var.env}-alb-sg"
  vpc_id = var.vpc_id
}

resource "aws_security_group" "task" {
  name   = "orderapi-${var.env}-task-sg"
  vpc_id = var.vpc_id
}

resource "aws_iam_role" "task" {
  name = "orderapi-${var.env}-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "exec" {
  name = "orderapi-${var.env}-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_ecr_repository" "orderapi" {
  name = "orderapi-${var.env}"
}
