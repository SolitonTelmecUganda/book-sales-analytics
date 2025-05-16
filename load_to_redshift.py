import argparse
import boto3
import redshift_connector
import os
from datetime import datetime


def get_s3_files(bucket_name, prefix):
    """Get list of files in S3 bucket with given prefix"""
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    if 'Contents' not in response:
        return []

    return [obj['Key'] for obj in response['Contents']]


def connect_to_redshift(host, database, user, password, port=5439):
    """Connect to Redshift database"""
    try:
        conn = redshift_connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        conn.autocommit = True
        print("Connected to Redshift successfully!")
        return conn
    except Exception as e:
        print(f"Error connecting to Redshift: {str(e)}")
        return None


def load_data_to_redshift(conn, s3_bucket, s3_path, table_name, iam_role):
    """Load data from S3 to Redshift table using COPY command"""
    cursor = conn.cursor()

    try:
        # Check if file exists in S3
        s3_client = boto3.client('s3')
        try:
            s3_client.head_object(Bucket=s3_bucket, Key=s3_path)
        except Exception as e:
            print(f"Error: S3 file s3://{s3_bucket}/{s3_path} does not exist or is not accessible.")
            return False

        # Build COPY command
        s3_uri = f"s3://{s3_bucket}/{s3_path}"
        copy_command = f"""
        COPY {table_name}
        FROM '{s3_uri}'
        IAM_ROLE '{iam_role}'
        CSV IGNOREHEADER 1
        REGION 'us-east-1'
        """

        print(f"Executing COPY command to load data into {table_name}...")
        cursor.execute(copy_command)

        # Get count of rows loaded
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Successfully loaded data into {table_name}. Total rows: {count}")
        return True
    except Exception as e:
        print(f"Error loading data to Redshift: {str(e)}")
        return False
    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser(description='Load data from S3 to Redshift')
    parser.add_argument('--host', required=True, help='Redshift host')
    parser.add_argument('--database', required=True, help='Redshift database name')
    parser.add_argument('--user', required=True, help='Redshift username')
    parser.add_argument('--password', required=True, help='Redshift password')
    parser.add_argument('--port', type=int, default=5439, help='Redshift port')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--iam-role', required=True, help='IAM role ARN for Redshift')
    args = parser.parse_args()

    # Connect to Redshift
    conn = connect_to_redshift(
        args.host, args.database, args.user, args.password, args.port
    )

    if not conn:
        return

    try:
        # Get today's date for S3 prefix
        today = datetime.now().strftime('%Y/%m/%d')

        # Load books data
        books_prefix = f"books/{today}/books.csv"
        load_data_to_redshift(
            conn,
            args.bucket,
            books_prefix,
            "analytics.dim_book",
            args.iam_role
        )

        # Load sales data
        sales_prefix = f"sales/{today}/sales.csv"
        load_data_to_redshift(
            conn,
            args.bucket,
            sales_prefix,
            "analytics.fact_sales",
            args.iam_role
        )

    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()