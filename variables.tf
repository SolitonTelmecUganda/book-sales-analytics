variable "aws_region" {
  description = "AWS Region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "booksales"
}

variable "environment" {
  description = "Environment (e.g. dev, staging, production)"
  type        = string
  default     = "production"
}

variable "redshift_db_name" {
  description = "Name of the Redshift database"
  type        = string
  default     = "analytics"
}

variable "redshift_username" {
  description = "Master username for Redshift"
  type        = string
  default     = "admin"
}

variable "redshift_password" {
  description = "Master password for Redshift"
  type        = string
  sensitive   = true
}

variable "redshift_node_type" {
  description = "Redshift node type"
  type        = string
  default     = "dc2.large"
}

variable "redshift_cluster_type" {
  description = "Redshift cluster type (single-node or multi-node)"
  type        = string
  default     = "single-node"
}

variable "redshift_nodes" {
  description = "Number of compute nodes in the Redshift cluster"
  type        = number
  default     = 1
}

variable "create_glue_resources" {
  description = "Whether to create AWS Glue resources"
  type        = bool
  default     = false
}