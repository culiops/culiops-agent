output "cluster_name"     { value = aws_ecs_cluster.main.name }
output "target_group_arn" { value = aws_lb_target_group.orderapi.arn }
output "task_role_arn"    { value = aws_iam_role.task.arn }
output "exec_role_arn"    { value = aws_iam_role.exec.arn }
output "ecr_repo_url"     { value = aws_ecr_repository.orderapi.repository_url }
output "task_subnets"     { value = var.private_subnets }
output "task_sg_id"       { value = aws_security_group.task.id }
