variable "region"          { type = string }
variable "env"             { type = string }
variable "vpc_id"          { type = string }
variable "public_subnets"  { type = list(string) }
variable "private_subnets" { type = list(string) }
variable "db_password" {
  type        = string
  sensitive   = true
  description = "Order DB master password handed to the service out-of-band; no resource in this stack consumes it."
}
