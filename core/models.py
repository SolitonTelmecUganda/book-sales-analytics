# models.py
from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    publisher = models.CharField(max_length=255, null=True, blank=True)
    genre = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='sales')
    quantity = models.IntegerField()
    sale_date = models.DateTimeField()
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=50)
    sale_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.book.title} - {self.sale_date}"