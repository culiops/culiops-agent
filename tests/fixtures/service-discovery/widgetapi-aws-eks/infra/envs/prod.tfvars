environment = "prod"
region      = "eu-west-1"

vpc_cidr             = "10.20.0.0/16"
availability_zones   = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
private_subnet_cidrs = ["10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24"]
public_subnet_cidrs  = ["10.20.101.0/24", "10.20.102.0/24", "10.20.103.0/24"]
single_nat_gateway   = false

db_instance_class         = "db.m6g.large"
db_replica_instance_class = "db.m6g.large"
db_allocated_storage      = 200
db_max_allocated_storage  = 1000
db_multi_az               = true
db_backup_retention_days  = 14

cache_node_type = "cache.r6g.large"
cache_num_nodes = 2

queue_visibility_timeout = 120
