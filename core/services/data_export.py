# services/data_export.py
import boto3
import pandas as pd
from io import StringIO
from django.conf import settings
from core.models import Book, Sale
from datetime import datetime, timedelta
import os
import csv
import random
from decimal import Decimal
import uuid
from faker import Faker


class DataWarehouseExporter:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_DATA_BUCKET

    def export_recent_sales(self, days=1):
        """Export recent sales data to S3"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Query recent sales with related book info
        sales = Sale.objects.filter(
            sale_date__gte=cutoff_date
        ).select_related('book')

        # Convert to DataFrame
        sales_data = [{
            'sale_id': sale.id,
            'book_id': sale.book.id,
            'title': sale.book.title,
            'isbn': sale.book.isbn,
            'quantity': sale.quantity,
            'sale_amount': float(sale.sale_amount),
            'sale_date': sale.sale_date.isoformat(),
            'region': sale.region,
            'customer_id': sale.customer_id
        } for sale in sales]

        df = pd.DataFrame(sales_data)

        if df.empty:
            return False

        # Save to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)

        # Upload to S3
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        file_key = f'sales/{date_prefix}/sales_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=csv_buffer.getvalue()
        )

        return file_key

    def generate_test_data(self, num_books=500, num_sales=10000):
        """Generate test data for development/testing"""
        fake = Faker()
        output_dir = os.path.join(settings.BASE_DIR, 'data')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        books_file = os.path.join(output_dir, 'books.csv')
        sales_file = os.path.join(output_dir, 'sales.csv')

        # Generate books
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

        publishers = [fake.company() for _ in range(20)]
        books = []

        with open(books_file, 'w', newline='') as csvfile:
            fieldnames = ['book_id', 'title', 'author', 'isbn', 'published_date', 'publisher', 'genre', 'price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for book_id in range(1, num_books + 1):
                if random.random() < 0.7:
                    title = fake.catch_phrase()
                else:
                    title = f"The {fake.word().capitalize()} of {fake.word().capitalize()}"

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

        # Generate sales
        regions = [
            "North America", "South America", "Europe", "Asia", "Africa",
            "Australia", "Middle East", "Caribbean", "Central America", "Pacific"
        ]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)

        with open(sales_file, 'w', newline='') as csvfile:
            fieldnames = ['sale_id', 'book_id', 'quantity', 'sale_date', 'customer_id', 'region', 'sale_amount']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for sale_id in range(1, num_sales + 1):
                book = random.choice(books)
                book_id = book['book_id']

                quantity = random.choices([1, 2, 3, 4, 5], weights=[70, 15, 10, 3, 2])[0]
                sale_date = fake.date_time_between(start_date=start_date, end_date=end_date)
                customer_id = str(uuid.uuid4())
                region = random.choice(regions)

                if random.random() < 0.3:
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

        # Upload to S3
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        books_key = f'books/{date_prefix}/books_test.csv'
        sales_key = f'sales/{date_prefix}/sales_test.csv'

        self.s3_client.upload_file(books_file, self.bucket_name, books_key)
        self.s3_client.upload_file(sales_file, self.bucket_name, sales_key)

        return {
            'books_file': books_file,
            'sales_file': sales_file,
            'books_key': books_key,
            'sales_key': sales_key,
            'num_books': num_books,
            'num_sales': num_sales
        }

    def load_to_redshift(self, books_key, sales_key):
        """Load data from S3 to Redshift"""
        try:
            import redshift_connector
        except ImportError:
            print("redshift_connector package not installed!")
            return False

        if not all([
            hasattr(settings, 'REDSHIFT_HOST'),
            hasattr(settings, 'REDSHIFT_DB'),
            hasattr(settings, 'REDSHIFT_USER'),
            hasattr(settings, 'REDSHIFT_PASSWORD'),
            hasattr(settings, 'REDSHIFT_IAM_ROLE')
        ]):
            print("Redshift settings not fully configured!")
            return False

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

            # Copy books data
            copy_books_command = f"""
            COPY analytics.dim_book
            FROM 's3://{self.bucket_name}/{books_key}'
            IAM_ROLE '{settings.REDSHIFT_IAM_ROLE}'
            CSV IGNOREHEADER 1
            REGION '{settings.AWS_REGION}'
            """
            cursor.execute(copy_books_command)

            # Copy sales data
            copy_sales_command = f"""
            COPY analytics.fact_sales
            FROM 's3://{self.bucket_name}/{sales_key}'
            IAM_ROLE '{settings.REDSHIFT_IAM_ROLE}'
            CSV IGNOREHEADER 1
            REGION '{settings.AWS_REGION}'
            """
            cursor.execute(copy_sales_command)

            # Get counts
            cursor.execute("SELECT COUNT(*) FROM analytics.dim_book")
            book_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM analytics.fact_sales")
            sales_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return {
                'book_count': book_count,
                'sales_count': sales_count,
                'success': True
            }
        except Exception as e:
            print(f"Error loading data to Redshift: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }