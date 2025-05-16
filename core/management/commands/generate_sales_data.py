# yourapp/management/commands/generate_sales_data.py
import csv
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import os
import boto3

from django.core.management.base import BaseCommand
from faker import Faker
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate fake sales data and optionally upload to S3 and Redshift'

    def add_arguments(self, parser):
        parser.add_argument('--books', type=int, default=500, help='Number of books to generate')
        parser.add_argument('--sales', type=int, default=10000, help='Number of sales records to generate')
        parser.add_argument('--skip-upload', action='store_true', help='Skip uploading to S3')
        parser.add_argument('--skip-redshift', action='store_true', help='Skip loading to Redshift')

    def handle(self, *args, **options):
        num_books = options['books']
        num_sales = options['sales']
        skip_upload = options['skip_upload']
        skip_redshift = options['skip_redshift']

        # Create output directory
        output_dir = os.path.join(settings.BASE_DIR, 'data')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        books_file = os.path.join(output_dir, 'books.csv')
        sales_file = os.path.join(output_dir, 'sales.csv')

        # Generate data
        self.stdout.write(self.style.NOTICE("Generating fake book sales data..."))
        books = self.generate_books(num_books, books_file)
        self.generate_sales(num_sales, books, sales_file)

        # Upload to S3 if requested
        if not skip_upload:
            self.stdout.write(self.style.NOTICE("Uploading data to S3..."))
            books_s3_key, sales_s3_key = self.upload_to_s3(books_file, sales_file)

            # Load to Redshift if requested
            if not skip_redshift and hasattr(settings, 'REDSHIFT_HOST'):
                self.stdout.write(self.style.NOTICE("Loading data to Redshift..."))
                self.load_to_redshift(books_s3_key, sales_s3_key)

        self.stdout.write(self.style.SUCCESS("Finished generating and processing data!"))

    def generate_books(self, num_books, output_file):
        """Generate book data and save to CSV"""
        fake = Faker()

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

        # Create publishers
        publishers = [fake.company() for _ in range(20)]

        # Generate books
        books = []
        book_ids = list(range(1, num_books + 1))

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['book_id', 'title', 'author', 'isbn', 'published_date', 'publisher', 'genre', 'price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for book_id in book_ids:
                # Generate title
                if random.random() < 0.7:
                    title = fake.catch_phrase()
                else:
                    title = f"The {fake.word().capitalize()} of {fake.word().capitalize()}"

                # Generate other fields
                author = fake.name()
                isbn = ''.join([str(random.randint(0, 9)) for _ in range(13)])
                published_date = fake.date_between(start_date='-20y', end_date='today')
                publisher = random.choice(publishers)
                genre = random.choice(book_genres)
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

        self.stdout.write(f"Generated {len(books)} books")
        return books

    def generate_sales(self, num_sales, books, output_file):
        """Generate sales data and save to CSV"""
        fake = Faker()

        # Regions for sales
        regions = [
            "North America", "South America", "Europe", "Asia", "Africa",
            "Australia", "Middle East", "Caribbean", "Central America", "Pacific"
        ]

        # Date range for sales (last 2 years)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['sale_id', 'book_id', 'quantity', 'sale_date', 'customer_id', 'region', 'sale_amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for sale_id in range(1, num_sales + 1):
                # Select random book
                book = random.choice(books)
                book_id = book['book_id']

                # Generate quantity (typically 1-5 books)
                quantity = random.choices([1, 2, 3, 4, 5], weights=[70, 15, 10, 3, 2])[0]

                # Generate sale date
                sale_date = fake.date_time_between(start_date=start_date, end_date=end_date)

                # Generate customer ID
                customer_id = str(uuid.uuid4())

                # Assign region
                region = random.choice(regions)

                # Calculate sale amount with occasional discount
                if random.random() < 0.3:  # 30% chance of discount
                    discount = Decimal(random.uniform(0.1, 0.4))
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
                    self.stdout.write(f"Generated {sale_id} sales records...")

        self.stdout.write(f"Generated {num_sales} sales records")

    def upload_to_s3(self, books_file, sales_file):
        """Upload generated files to S3"""
        if not hasattr(settings, 'AWS_DATA_BUCKET'):
            self.stdout.write(self.style.ERROR("AWS_DATA_BUCKET not defined in settings!"))
            return None, None

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # Generate date-based prefix for S3
        today = datetime.now().strftime('%Y/%m/%d')

        # Upload books data
        books_s3_key = f"books/{today}/books.csv"
        try:
            s3_client.upload_file(books_file, settings.AWS_DATA_BUCKET, books_s3_key)
            self.stdout.write(f"Uploaded books.csv to s3://{settings.AWS_DATA_BUCKET}/{books_s3_key}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error uploading books data: {str(e)}"))
            books_s3_key = None

        # Upload sales data
        sales_s3_key = f"sales/{today}/sales.csv"
        try:
            s3_client.upload_file(sales_file, settings.AWS_DATA_BUCKET, sales_s3_key)
            self.stdout.write(f"Uploaded sales.csv to s3://{settings.AWS_DATA_BUCKET}/{sales_s3_key}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error uploading sales data: {str(e)}"))
            sales_s3_key = None

        return books_s3_key, sales_s3_key

    def load_to_redshift(self, books_s3_key, sales_s3_key):
        """Load data from S3 to Redshift"""
        try:
            import redshift_connector
        except ImportError:
            self.stdout.write(self.style.ERROR("redshift_connector package not installed!"))
            self.stdout.write(self.style.NOTICE("Install with: pip install redshift-connector"))
            return

        if not all([
            hasattr(settings, 'REDSHIFT_HOST'),
            hasattr(settings, 'REDSHIFT_DB'),
            hasattr(settings, 'REDSHIFT_USER'),
            hasattr(settings, 'REDSHIFT_PASSWORD'),
            hasattr(settings, 'REDSHIFT_IAM_ROLE')
        ]):
            self.stdout.write(self.style.ERROR("Redshift settings not fully configured!"))
            return

        # Connect to Redshift
        try:
            conn = redshift_connector.connect(
                host=settings.REDSHIFT_HOST,
                database=settings.REDSHIFT_DB,
                user=settings.REDSHIFT_USER,
                password=settings.REDSHIFT_PASSWORD,
                port=getattr(settings, 'REDSHIFT_PORT', 5439)
            )
            conn.autocommit = True
            cursor = conn.cursor()
            self.stdout.write("Connected to Redshift successfully!")

            # Create schema and tables if they don't exist
            self.create_redshift_schema(cursor)

            # Load books data
            if books_s3_key:
                self.copy_to_redshift(
                    cursor,
                    settings.AWS_DATA_BUCKET,
                    books_s3_key,
                    "analytics.dim_book",
                    settings.REDSHIFT_IAM_ROLE
                )

            # Load sales data
            if sales_s3_key:
                self.copy_to_redshift(
                    cursor,
                    settings.AWS_DATA_BUCKET,
                    sales_s3_key,
                    "analytics.fact_sales",
                    settings.REDSHIFT_IAM_ROLE
                )

            cursor.close()
            conn.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error connecting to Redshift: {str(e)}"))

    def create_redshift_schema(self, cursor):
        """Create the Redshift schema and tables if they don't exist"""
        try:
            # Create schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics")

            # Create dimension table for books
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS analytics.dim_book
                           (
                               book_id        INT PRIMARY KEY,
                               title          VARCHAR(255),
                               author         VARCHAR(255),
                               isbn           VARCHAR(13),
                               published_date DATE,
                               publisher      VARCHAR(255),
                               genre          VARCHAR(100),
                               price          DECIMAL(10, 2)
                           )
                           """)

            # Create fact table for sales
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS analytics.fact_sales
                           (
                               sale_id     INT PRIMARY KEY,
                               book_id     INT,
                               quantity    INT,
                               sale_date   TIMESTAMP,
                               customer_id VARCHAR(100),
                               region      VARCHAR(50),
                               sale_amount DECIMAL(10, 2)
                           )
                           """)

            # Create views
            self.create_redshift_views(cursor)

            self.stdout.write("Created Redshift schema and tables")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating Redshift schema: {str(e)}"))

    def create_redshift_views(self, cursor):
        """Create analytics views in Redshift"""
        try:
            # Sales by day view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.sales_by_day AS
                           SELECT DATE_TRUNC('day', sale_date)::DATE AS day,
                                  COUNT(*)                           AS num_sales,
                                  SUM(quantity)                      AS total_books_sold,
                                  SUM(sale_amount)                   AS total_revenue
                           FROM analytics.fact_sales
                           GROUP BY DATE_TRUNC('day', sale_date)::DATE
                           ORDER BY day
                           """)

            # Sales by region view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.sales_by_region AS
                           SELECT region,
                                  SUM(sale_amount) AS total_revenue,
                                  COUNT(*)         AS transaction_count,
                                  SUM(quantity)    AS books_sold
                           FROM analytics.fact_sales
                           GROUP BY region
                           ORDER BY total_revenue DESC
                           """)

            # Top books view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.top_books AS
                           SELECT b.book_id,
                                  b.title,
                                  b.author,
                                  b.genre,
                                  COUNT(s.sale_id)   AS num_sales,
                                  SUM(s.quantity)    AS total_quantity,
                                  SUM(s.sale_amount) AS total_revenue
                           FROM analytics.dim_book b
                                    JOIN analytics.fact_sales s ON b.book_id = s.book_id
                           GROUP BY b.book_id, b.title, b.author, b.genre
                           ORDER BY total_revenue DESC
                           """)

            # Sales by genre view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.sales_by_genre AS
                           SELECT b.genre,
                                  COUNT(s.sale_id)   AS num_sales,
                                  SUM(s.quantity)    AS total_quantity,
                                  SUM(s.sale_amount) AS total_revenue
                           FROM analytics.dim_book b
                                    JOIN analytics.fact_sales s ON b.book_id = s.book_id
                           GROUP BY b.genre
                           ORDER BY total_revenue DESC
                           """)

            # Monthly sales view
            cursor.execute("""
                           CREATE OR REPLACE VIEW analytics.monthly_sales AS
                           SELECT DATE_TRUNC('month', sale_date)::DATE AS month,
                                  COUNT(*)                             AS num_sales,
                                  SUM(quantity)                        AS total_books_sold,
                                  SUM(sale_amount)                     AS total_revenue
                           FROM analytics.fact_sales
                           GROUP BY DATE_TRUNC('month', sale_date)::DATE
                           ORDER BY month
                           """)

            self.stdout.write("Created Redshift views")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating Redshift views: {str(e)}"))

    def copy_to_redshift(self, cursor, bucket, key, table, iam_role):
        """Copy data from S3 to Redshift using COPY command"""
        try:
            # Build COPY command
            s3_uri = f"s3://{bucket}/{key}"
            copy_command = f"""
            COPY {table}
            FROM '{s3_uri}'
            IAM_ROLE '{iam_role}'
            CSV IGNOREHEADER 1
            REGION '{settings.AWS_REGION}'
            """

            # Execute COPY command
            self.stdout.write(f"Copying data from {s3_uri} to {table}...")
            cursor.execute(copy_command)

            # Get count of rows loaded
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f"Successfully loaded {count} rows into {table}"))

            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error copying data to Redshift: {str(e)}"))
            return False