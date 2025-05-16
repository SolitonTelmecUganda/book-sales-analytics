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
NUM_BOOKS = 5000  # Generate 500 unique books
NUM_SALES = 10000000  # Generate 10,000 sales transactions

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