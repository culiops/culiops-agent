environment = "staging"
region      = "eu-west-1"

vpc_cidr             = "10.30.0.0/16"
availability_zones   = ["eu-west-1a", "eu-west-1b"]
private_subnet_cidrs = ["10.30.1.0/24", "10.30.2.0/24"]
public_subnet_cidrs  = ["10.30.101.0/24", "10.30.102.0/24"]
single_nat_gateway   = true

db_instance_class         = "db.t4g.medium"
db_replica_instance_class = "db.t4g.medium"
db_allocated_storage      = 50
db_max_allocated_storage  = 200
db_multi_az               = false
db_backup_retention_days  = 3

cache_node_type = "cache.t4g.small"
cache_num_nodes = 1

queue_visibility_timeout = 60
