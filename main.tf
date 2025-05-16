provider "aws" {
  region = var.aws_region
}

# S3 for Raw Data
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data"
}

# S3 bucket ACL (separate resource per deprecation warning)
resource "aws_s3_bucket_acl" "raw_data_acl" {
  bucket = aws_s3_bucket.raw_data.id
  acl    = "private"
}

# S3 bucket versioning (separate resource per deprecation warning)
resource "aws_s3_bucket_versioning" "raw_data_versioning" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption (separate resource per deprecation warning)
resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data_encryption" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# VPC for Redshift and related resources
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Subnet for Redshift
resource "aws_subnet" "redshift_subnet_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-subnet-1"
  }
}

resource "aws_subnet" "redshift_subnet_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-subnet-2"
  }
}

# Create a security group for Redshift
resource "aws_security_group" "redshift" {
  name        = "${var.project_name}-redshift-sg"
  description = "Security group for Redshift cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Redshift port"
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # In production, restrict this to your app's IP
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-redshift-sg"
  }
}

# Create a subnet group for Redshift
resource "aws_redshift_subnet_group" "redshift_subnet_group" {
  name       = "${var.project_name}-redshift-subnet-group"
  subnet_ids = [aws_subnet.redshift_subnet_1.id, aws_subnet.redshift_subnet_2.id]

  tags = {
    Name = "${var.project_name}-redshift-subnet-group"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-public-route-table"
  }
}

# Route table association
resource "aws_route_table_association" "subnet_1_association" {
  subnet_id      = aws_subnet.redshift_subnet_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "subnet_2_association" {
  subnet_id      = aws_subnet.redshift_subnet_2.id
  route_table_id = aws_route_table.public.id
}

# Redshift Cluster
resource "aws_redshift_cluster" "analytics" {
  cluster_identifier        = "${var.project_name}-analytics"
  database_name             = var.redshift_db_name
  master_username           = var.redshift_username
  master_password           = var.redshift_password
  node_type                 = var.redshift_node_type
  cluster_type              = var.redshift_cluster_type
  number_of_nodes           = var.redshift_nodes
  skip_final_snapshot       = true
  automated_snapshot_retention_period = 7
  encrypted                 = true

  vpc_security_group_ids    = [aws_security_group.redshift.id]
  cluster_subnet_group_name = aws_redshift_subnet_group.redshift_subnet_group.name

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Redshift to access S3
resource "aws_iam_role" "redshift_s3_role" {
  name = "${var.project_name}-redshift-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "redshift_s3_policy" {
  name   = "${var.project_name}-redshift-s3-access"
  role   = aws_iam_role.redshift_s3_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:List*"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.raw_data.arn}",
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
      }
    ]
  })
}

# IAM Role for Glue jobs
resource "aws_iam_role" "glue_job_role" {
  count = var.create_glue_resources ? 1 : 0
  name = "${var.project_name}-glue-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  count = var.create_glue_resources ? 1 : 0
  role       = aws_iam_role.glue_job_role[0].id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_policy" {
  count = var.create_glue_resources ? 1 : 0
  name   = "${var.project_name}-glue-s3-access"
  role   = aws_iam_role.glue_job_role[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:List*"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.raw_data.arn}",
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
      }
    ]
  })
}

# Glue Job for ETL
resource "aws_glue_job" "sales_etl" {
  count = var.create_glue_resources ? 1 : 0
  name         = "${var.project_name}-sales-etl"
  role_arn     = aws_iam_role.glue_job_role[0].arn
  glue_version = "3.0"

  command {
    script_location = "s3://${aws_s3_bucket.raw_data.bucket}/scripts/sales_etl.py"
  }

  default_arguments = {
    "--job-language"               = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-job-insights"        = "true"
  }
}

# Outputs
output "redshift_endpoint" {
  value = aws_redshift_cluster.analytics.endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.raw_data.bucket
}

output "redshift_jdbc_url" {
  value = "jdbc:redshift://${aws_redshift_cluster.analytics.endpoint}:5439/${var.redshift_db_name}"
}