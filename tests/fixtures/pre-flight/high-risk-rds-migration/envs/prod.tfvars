env               = "prod"
db_subnet_group   = "userdb-prod-subnet-group"
db_instance_class = "db.r6g.large"
vpc_id            = "vpc-0abc123def456789"
app_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
