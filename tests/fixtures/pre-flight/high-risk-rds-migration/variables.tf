variable "env" {
  type = string
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_subnet_group" {
  type = string
}

variable "db_instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "vpc_id" {
  type = string
}

variable "app_subnet_cidrs" {
  type = list(string)
}
