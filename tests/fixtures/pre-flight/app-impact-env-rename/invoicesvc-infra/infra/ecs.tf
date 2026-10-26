# invoicesvc task definition (AFTER the proposed change)

resource "aws_ecs_task_definition" "invoicesvc" {
  family                   = "invoicesvc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  task_role_arn            = aws_iam_role.invoicesvc_task.arn
  execution_role_arn       = aws_iam_role.invoicesvc_exec.arn

  container_definitions = jsonencode([{
    name         = "invoicesvc"
    image        = "${var.ecr_repo}:${var.image_tag}"
    portMappings = [{ containerPort = 9090 }]
    environment = [
      { name = "HTTP_PORT", value = "9090" },
      { name = "INVOICE_BUCKET_NAME", value = aws_s3_bucket.invoices.bucket },
      { name = "PDF_RENDER_TIMEOUT_SECONDS", value = "20" },
    ]
  }])
}
