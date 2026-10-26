# cartapi task role — inline publish policy (AFTER the proposed change)

resource "aws_iam_role_policy" "cartapi_task_publish" {
  name = "cartapi-publish"
  role = aws_iam_role.cartapi_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowSNSPublishCartEvents"
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = [aws_sns_topic.cart_events.arn]
      },
    ]
  })
}
