terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }

  backend "s3" {
    bucket = "widgetapi-tfstate"
    key    = "platform/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "widgetapi"
      Environment = var.environment
      ManagedBy   = "terraform"
      Stack       = "platform"
    }
  }
}

locals {
  name_prefix = "widgetapi-${var.environment}"
}

# Cross-stack dependency on the infra stack (VPC, subnets, bucket, queue ARNs).
data "terraform_remote_state" "infra" {
  backend = "s3"

  config = {
    bucket = "widgetapi-tfstate"
    key    = "infra/terraform.tfstate"
    region = var.region
  }
}

# ---------------------------------------------------------------------------
# EKS cluster
# ---------------------------------------------------------------------------

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.8"

  cluster_name    = local.name_prefix
  cluster_version = var.eks_version

  vpc_id                   = data.terraform_remote_state.infra.outputs.vpc_id
  subnet_ids               = data.terraform_remote_state.infra.outputs.private_subnet_ids
  control_plane_subnet_ids = data.terraform_remote_state.infra.outputs.private_subnet_ids

  cluster_endpoint_public_access = true

  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size

      labels = {
        role = "workload"
      }
    }
  }

  cluster_addons = {
    vpc-cni                = {}
    coredns                = {}
    kube-proxy             = {}
    aws-ebs-csi-driver     = {}
  }
}

# ---------------------------------------------------------------------------
# IRSA: pod identity for widgetapi workload (S3 + SQS + Secrets Manager)
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "widgetapi_workload" {
  statement {
    sid    = "S3UploadsAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      data.terraform_remote_state.infra.outputs.uploads_bucket_arn,
      "${data.terraform_remote_state.infra.outputs.uploads_bucket_arn}/*",
    ]
  }

  statement {
    sid    = "SQSAsyncAccess"
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
    ]
    resources = [
      data.terraform_remote_state.infra.outputs.async_queue_arn,
    ]
  }

  statement {
    sid    = "SecretsManagerDBPassword"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      data.terraform_remote_state.infra.outputs.db_secret_arn,
    ]
  }
}

resource "aws_iam_policy" "widgetapi_workload" {
  name   = "${local.name_prefix}-workload"
  policy = data.aws_iam_policy_document.widgetapi_workload.json
}

module "widgetapi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.39"

  role_name = "${local.name_prefix}-workload"

  role_policy_arns = {
    workload = aws_iam_policy.widgetapi_workload.arn
  }

  oidc_providers = {
    eks = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["widgetapi:widgetapi"]
    }
  }
}

# ---------------------------------------------------------------------------
# ALB (public) — target group populated by the ingress controller
# ---------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name   = "${local.name_prefix}-alb-sg"
  vpc_id = data.terraform_remote_state.infra.outputs.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "alb" {
  name               = "${local.name_prefix}-alb"
  load_balancer_type = "application"
  subnets            = data.terraform_remote_state.infra.outputs.public_subnet_ids
  security_groups    = [aws_security_group.alb.id]

  enable_deletion_protection = var.environment == "prod"
  idle_timeout               = 60
}

# ---------------------------------------------------------------------------
# CloudFront distribution fronting the ALB for asset routes
# ---------------------------------------------------------------------------

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${local.name_prefix} CDN"
  default_root_object = ""
  price_class         = var.environment == "prod" ? "PriceClass_All" : "PriceClass_100"

  origin {
    domain_name = aws_lb.alb.dns_name
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Host"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 60
    max_ttl     = 3600
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
