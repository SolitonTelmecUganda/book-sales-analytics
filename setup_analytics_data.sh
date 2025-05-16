#!/bin/bash
# setup_analytics_data.sh - Generate fake data and load it to S3 and Redshift

# Check for required commands
command -v python >/dev/null 2>&1 || { echo "Python is required but not installed. Aborting."; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "pip is required but not installed. Aborting."; exit 1; }

# Check for required arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <s3-bucket-name> <redshift-host> [additional options]"
    echo ""
    echo "Required:"
    echo "  <s3-bucket-name>   Name of the S3 bucket to store data"
    echo "  <redshift-host>    Redshift cluster endpoint"
    echo ""
    echo "Optional:"
    echo "  --database NAME    Redshift database name (default: analytics)"
    echo "  --user NAME        Redshift username (default: admin)"
    echo "  --password PWD     Redshift password (will prompt if not provided)"
    echo "  --iam-role ARN     IAM role ARN for Redshift (required for loading data)"
    echo "  --skip-generate    Skip generating new data"
    echo "  --skip-upload      Skip uploading to S3"
    echo "  --skip-redshift    Skip loading to Redshift"
    exit 1
fi

# Parse arguments
S3_BUCKET=$1
REDSHIFT_HOST=$2
shift 2

# Default values
REDSHIFT_DB="analytics"
REDSHIFT_USER="admin"
REDSHIFT_PASSWORD=""
IAM_ROLE=""
SKIP_GENERATE=false
SKIP_UPLOAD=false
SKIP_REDSHIFT=false

# Parse optional arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        --database)
            REDSHIFT_DB="$2"
            shift 2
            ;;
        --user)
            REDSHIFT_USER="$2"
            shift 2
            ;;
        --password)
            REDSHIFT_PASSWORD="$2"
            shift 2
            ;;
        --iam-role)
            IAM_ROLE="$2"
            shift 2
            ;;
        --skip-generate)
            SKIP_GENERATE=true
            shift
            ;;
        --skip-upload)
            SKIP_UPLOAD=true
            shift
            ;;
        --skip-redshift)
            SKIP_REDSHIFT=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if password is needed and not provided
if [ "$SKIP_REDSHIFT" = false ] && [ -z "$REDSHIFT_PASSWORD" ]; then
    echo -n "Enter Redshift password: "
    read -s REDSHIFT_PASSWORD
    echo ""
fi

# Check for IAM role if loading to Redshift
if [ "$SKIP_REDSHIFT" = false ] && [ -z "$IAM_ROLE" ]; then
    echo "Error: IAM role ARN is required for loading data to Redshift."
    echo "Please provide with --iam-role parameter."
    exit 1
fi

# Install required packages
echo "Installing required Python packages..."
pip install faker boto3 redshift-connector

# Generate data if not skipped
if [ "$SKIP_GENERATE" = false ]; then
    echo "Generating fake book sales data..."
    python - <<EOF
import csv
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
import os

# Initialize Faker
fake = Faker()

# Configure output path
output_dir = "data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Output files
books_file = os.path.join(output_dir, "books.csv")
sales_file = os.path.join(output_dir, "sales.csv")

# Constants
NUM_BOOKS = 500  # Generate 500 unique books
NUM_SALES = 10000  # Generate 10,000 sales transactions

# Book categories/genres
book_genres = [
    "Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller",
    "Romance", "Western", "Dystopian", "Contemporary", "Historical Fiction",
    "Horror", "Young Adult", "Children's", "Biography", "Autobiography",
    "Memoir", "Cooking", "Art", "Self-help", "Development",
    "Motivational", "Health", "History", "Travel", "Guide",
    "Science", "Math", "Religion", "Spirituality", "True Crime",
    "Humor", "Essay", "Parenting", "Relationships", "Technology",
    "Business", "Economics", "Philosophy", "Psychology", "Politics"
]

# Regions for sales
regions = [
    "North America", "South America", "Europe", "Asia", "Africa",
    "Australia", "Middle East", "Caribbean", "Central America", "Pacific"
]

# Create publishers
publishers = [
    fake.company() for _ in range(20)
]

# Helper function to generate an ISBN-13
def generate_isbn13():
    # Generate 12 digits (real ISBN-13 has complex checksum algorithm)
    digits = [str(random.randint(0, 9)) for _ in range(12)]
    # Add a simple checksum digit
    checksum = sum(int(d) for d in digits) % 10
    digits.append(str(checksum))
    return ''.join(digits)

# Generate books data
print("Generating books data...")
books = []
book_ids = list(range(1, NUM_BOOKS + 1))

with open(books_file, 'w', newline='') as csvfile:
    fieldnames = ['book_id', 'title', 'author', 'isbn', 'published_date', 'publisher', 'genre', 'price']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for book_id in book_ids:
        # Generate a realistic book title
        if random.random() < 0.7:
            # 70% chance of a standard title format
            title = fake.catch_phrase()
        else:
            # 30% chance of a "The X of Y" format
            title = f"The {fake.word().capitalize()} of {fake.word().capitalize()}"

        # Generate author name
        author = fake.name()

        # Generate ISBN
        isbn = generate_isbn13()

        # Generate publication date (within last 20 years)
        published_date = fake.date_between(start_date='-20y', end_date='today')

        # Assign a publisher
        publisher = random.choice(publishers)

        # Assign a genre
        genre = random.choice(book_genres)

        # Generate price (between $4.99 and $59.99)
        price = round(Decimal(random.uniform(4.99, 59.99)), 2)

        book = {
            'book_id': book_id,
            'title': title,
            'author': author,
            'isbn': isbn,
            'published_date': published_date.strftime('%Y-%m-%d'),
            'publisher': publisher,
            'genre': genre,
            'price': price
        }
        books.append(book)
        writer.writerow(book)

print(f"Generated {len(books)} books and saved to {books_file}")

# Generate sales data
print("Generating sales data...")

# Date range for sales (last 2 years)
end_date = datetime.now()
start_date = end_date - timedelta(days=730)  # Approximately 2 years

with open(sales_file, 'w', newline='') as csvfile:
    fieldnames = ['sale_id', 'book_id', 'quantity', 'sale_date', 'customer_id', 'region', 'sale_amount']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for sale_id in range(1, NUM_SALES + 1):
        # Select a random book
        book = random.choice(books)
        book_id = book['book_id']

        # Generate quantity (typically 1-5 books)
        quantity = random.choices([1, 2, 3, 4, 5], weights=[70, 15, 10, 3, 2])[0]

        # Generate sale date
        sale_date = fake.date_time_between(start_date=start_date, end_date=end_date)

        # Generate customer ID (anonymous UUID)
        customer_id = str(uuid.uuid4())

        # Assign a region
        region = random.choice(regions)

        # Calculate sale amount (book price * quantity) with occasional discount
        if random.random() < 0.3:  # 30% chance of discount
            discount = Decimal(random.uniform(0.1, 0.4))  # 10-40% discount
            sale_amount = round(Decimal(book['price']) * quantity * (1 - discount), 2)
        else:
            sale_amount = round(Decimal(book['price']) * quantity, 2)

        sale = {
            'sale_id': sale_id,
            'book_id': book_id,
            'quantity': quantity,
            'sale_date': sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            'customer_id': customer_id,
            'region': region,
            'sale_amount': sale_amount
        }
        writer.writerow(sale)

        # Progress indicator
        if sale_id % 1000 == 0:
            print(f"Generated {sale_id} sales records...")

print(f"Generated {NUM_SALES} sales records and saved to {sales_file}")
print("Data generation complete!")
EOF
fi

# Upload to S3 if not skipped
if [ "$SKIP_UPLOAD" = false ]; then
    echo "Uploading data to S3 bucket $S3_BUCKET..."
    python - <<EOF
import boto3
import os
from datetime import datetime

# Variables from shell script
bucket_name = "$S3_BUCKET"
data_dir = "data"

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

# Generate date-based prefix for S3
today = datetime.now().strftime('%Y/%m/%d')

# Upload books data
books_file = os.path.join(data_dir, 'books.csv')
if os.path.exists(books_file):
    upload_to_s3(bucket_name, books_file, f"books/{today}")
else:
    print(f"Books file {books_file} not found!")

# Upload sales data
sales_file = os.path.join(data_dir, 'sales.csv')
if os.path.exists(sales_file):
    upload_to_s3(bucket_name, sales_file, f"sales/{today}")
else:
    print(f"Sales file {sales_file} not found!")

print("Upload complete!")
EOF
fi

# Load data to Redshift if not skipped
if [ "$SKIP_REDSHIFT" = false ]; then
    echo "Creating schema and tables in Redshift..."
    python - <<EOF
import redshift_connector

# Connection details
host = "$REDSHIFT_HOST"
database = "$REDSHIFT_DB"
user = "$REDSHIFT_USER"
password = "$REDSHIFT_PASSWORD"

# Connect to Redshift
try:
    conn = redshift_connector.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected to Redshift successfully!")

    # Create schema and tables
    sql = """
    -- Create schema (if not exists)
    CREATE SCHEMA IF NOT EXISTS analytics;

    -- Drop existing tables if needed
    DROP TABLE IF EXISTS analytics.fact_sales;
    DROP TABLE IF EXISTS analytics.dim_book;

    -- Create dimension table for books
    CREATE TABLE analytics.dim_book (
        book_id INT PRIMARY KEY,
        title VARCHAR(255),
        author VARCHAR(255),
        isbn VARCHAR(13),
        published_date DATE,
        publisher VARCHAR(255),
        genre VARCHAR(100),
        price DECIMAL(10, 2)
    );

    -- Create fact table for sales
    CREATE TABLE analytics.fact_sales (
        sale_id INT PRIMARY KEY,
        book_id INT,
        quantity INT,
        sale_date TIMESTAMP,
        customer_id VARCHAR(100),
        region VARCHAR(50),
        sale_amount DECIMAL(10, 2)
    );

    -- Create aggregated views for dashboards
    CREATE OR REPLACE VIEW analytics.sales_by_day AS
    SELECT
        DATE_TRUNC('day', sale_date)::DATE AS day,
        COUNT(*) AS num_sales,
        SUM(quantity) AS total_books_sold,
        SUM(sale_amount) AS total_revenue
    FROM analytics.fact_sales
    GROUP BY DATE_TRUNC('day', sale_date)::DATE
    ORDER BY day;

    CREATE OR REPLACE VIEW analytics.sales_by_region AS
    SELECT
        region,
        SUM(sale_amount) AS total_revenue,
        COUNT(*) AS transaction_count,
        SUM(quantity) AS books_sold
    FROM analytics.fact_sales
    GROUP BY region
    ORDER BY total_revenue DESC;

    CREATE OR REPLACE VIEW analytics.top_books AS
    SELECT
        b.book_id,
        b.title,
        b.author,
        b.genre,
        COUNT(s.sale_id) AS num_sales,
        SUM(s.quantity) AS total_quantity,
        SUM(s.sale_amount) AS total_revenue
    FROM analytics.dim_book b
    JOIN analytics.fact_sales s ON b.book_id = s.book_id
    GROUP BY b.book_id, b.title, b.author, b.genre
    ORDER BY total_revenue DESC;

    CREATE OR REPLACE VIEW analytics.sales_by_genre AS
    SELECT
        b.genre,
        COUNT(s.sale_id) AS num_sales,
        SUM(s.quantity) AS total_quantity,
        SUM(s.sale_amount) AS total_revenue
    FROM analytics.dim_book b
    JOIN analytics.fact_sales s ON b.book_id = s.book_id
    GROUP BY b.genre
    ORDER BY total_revenue DESC;

    -- Create view for monthly trends
    CREATE OR REPLACE VIEW analytics.monthly_sales AS
    SELECT
        DATE_TRUNC('month', sale_date)::DATE AS month,
        COUNT(*) AS num_sales,
        SUM(quantity) AS total_books_sold,
        SUM(sale_amount) AS total_revenue
    FROM analytics.fact_sales
    GROUP BY DATE_TRUNC('month', sale_date)::DATE
    ORDER BY month;
    """

    cursor.execute(sql)
    print("Schema and tables created successfully!")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error creating schema in Redshift: {str(e)}")
    exit(1)
EOF

    echo "Loading data from S3 to Redshift..."
    python - <<EOF
import boto3
import redshift_connector
from datetime import datetime

# Variables from shell script
redshift_host = "$REDSHIFT_HOST"
redshift_db = "$REDSHIFT_DB"
redshift_user = "$REDSHIFT_USER"
redshift_password = "$REDSHIFT_PASSWORD"
bucket_name = "$S3_BUCKET"
iam_role = "$IAM_ROLE"

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

# Connect to Redshift
conn = connect_to_redshift(
    redshift_host, redshift_db, redshift_user, redshift_password
)

if not conn:
    exit(1)

try:
    # Get today's date for S3 prefix
    today = datetime.now().strftime('%Y/%m/%d')

    # Load books data
    books_prefix = f"books/{today}/books.csv"
    load_data_to_redshift(
        conn,
        bucket_name,
        books_prefix,
        "analytics.dim_book",
        iam_role
    )

    # Load sales data
    sales_prefix = f"sales/{today}/sales.csv"
    load_data_to_redshift(
        conn,
        bucket_name,
        sales_prefix,
        "analytics.fact_sales",
        iam_role
    )

finally:
    conn.close()
    print("Connection closed.")
EOF
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Connect your Django app to the data warehouse"
echo "2. Update your views to use the data from Redshift"
echo "3. Build your React dashboard components"
echo ""
echo "Redshift Connection Details:"
echo "Host: $REDSHIFT_HOST"
echo "Database: $REDSHIFT_DB"
echo "Username: $REDSHIFT_USER"
echo "Port: 5439"