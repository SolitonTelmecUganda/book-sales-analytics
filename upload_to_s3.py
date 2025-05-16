import boto3
import os
import argparse
from datetime import datetime


def upload_to_s3(bucket_name, local_file_path, s3_prefix=None):
    """
    Upload a file to an S3 bucket

    :param bucket_name: S3 bucket name
    :param local_file_path: Path to local file
    :param s3_prefix: S3 key prefix (folder path)
    :return: S3 URL of uploaded file
    """
    # Extract filename from path
    filename = os.path.basename(local_file_path)

    # Create S3 key (path in S3)
    if s3_prefix:
        s3_key = f"{s3_prefix}/{filename}"
    else:
        s3_key = filename

    # Create S3 client
    s3_client = boto3.client('s3')

    try:
        # Upload file
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        print(f"Successfully uploaded {filename} to s3://{bucket_name}/{s3_key}")
        return f"s3://{bucket_name}/{s3_key}"
    except Exception as e:
        print(f"Error uploading {filename} to S3: {str(e)}")
        return None


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Upload generated data to S3 bucket')
    parser.add_argument('bucket_name', help='S3 bucket name')
    parser.add_argument('--data-dir', default='data', help='Directory containing generated data files')
    args = parser.parse_args()

    # Check if data directory exists
    if not os.path.exists(args.data_dir):
        print(f"Data directory {args.data_dir} does not exist!")
        return

    # Generate date-based prefix for S3
    today = datetime.now().strftime('%Y/%m/%d')

    # Upload books data
    books_file = os.path.join(args.data_dir, 'books.csv')
    if os.path.exists(books_file):
        upload_to_s3(args.bucket_name, books_file, f"books/{today}")
    else:
        print(f"Books file {books_file} not found!")

    # Upload sales data
    sales_file = os.path.join(args.data_dir, 'sales.csv')
    if os.path.exists(sales_file):
        upload_to_s3(args.bucket_name, sales_file, f"sales/{today}")
    else:
        print(f"Sales file {sales_file} not found!")

    print("Upload complete!")


if __name__ == "__main__":
    main()