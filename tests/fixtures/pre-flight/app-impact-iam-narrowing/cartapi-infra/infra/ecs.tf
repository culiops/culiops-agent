resource "aws_ecs_task_definition" "cartapi" {
  family                   = "cartapi"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  task_role_arn            = aws_iam_role.cartapi_task.arn
  execution_role_arn       = aws_iam_role.cartapi_exec.arn

  container_definitions = jsonencode([{
    name  = "cartapi"
    image = "${var.ecr_repo}:${var.image_tag}"
    portMappings = [{ containerPort = 8080 }]
    environment = [
      { name = "PORT", value = "8080" },
      { name = "CART_EVENTS_TOPIC_ARN", value = aws_sns_topic.cart_events.arn },
      { name = "LEDGER_QUEUE_URL", value = aws_sqs_queue.ledger.url },
    ]
  }])
}

resource "aws_sqs_queue" "ledger" {
  name                        = "cartapi-ledger.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
}
