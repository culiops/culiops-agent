# TEST FIXTURE — INTENTIONALLY UNSAFE. This models a change that caches per-user
# responses at the edge, so pre-flight can be checked against it. Do not deploy.
# shopfront distribution (AFTER the proposed change)

locals {
  cache_policy_caching_optimized   = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Managed-CachingOptimized
  cache_policy_caching_disabled    = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # Managed-CachingDisabled
  origin_request_policy_all_viewer = "216adef6-5c7f-47e4-b989-5492eafa07d3" # Managed-AllViewer
}

resource "aws_cloudfront_distribution" "shopfront" {
  enabled         = true
  is_ipv6_enabled = true
  aliases         = ["shop.example.com"]

  origin {
    origin_id   = "api-alb"
    domain_name = aws_lb.api.dns_name
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id         = "api-alb"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = local.cache_policy_caching_disabled
    origin_request_policy_id = local.origin_request_policy_all_viewer
  }

  ordered_cache_behavior {
    path_pattern             = "/api/catalog/*"
    target_origin_id         = "api-alb"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = local.cache_policy_caching_optimized
    origin_request_policy_id = local.origin_request_policy_all_viewer
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
