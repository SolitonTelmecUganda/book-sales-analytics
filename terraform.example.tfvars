aws_region = # Change to your preferred region
project_name = # Change to your project name
environment = "production"
redshift_db_name = # Change to your database name
redshift_username = # Change to your Redshift username
redshift_password = # Change to your Redshift password
redshift_node_type = "dc2.large"
redshift_cluster_type = "single-node"  # Use "multi-node" for production
redshift_nodes = 1  # Increase for production
create_glue_resources = false  # Set to true if you have Glue permissions