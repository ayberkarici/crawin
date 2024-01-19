from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
import uuid
from django.contrib.auth.models import User

class Shop(models.Model):
    name = models.CharField(max_length=255)
    announcement = models.TextField(blank=True, null=True)
    comment_count = models.IntegerField(default=0, blank=True, null=True)
    total_sales = models.IntegerField(default=0, blank=True, null=True)
    logo_url = models.URLField(max_length=1024, blank=True, null=True)
    admirers_count = models.IntegerField(default=0, blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    last_updated_announcement = models.DateTimeField(null=True, blank=True)
    star_count = models.FloatField(
        default=0,
        validators=[
            MaxValueValidator(5),  # Maksimum yıldız sayısı 100 olarak belirlendi
            MinValueValidator(0)     # Minimum yıldız sayısı 0 olarak belirlendi
        ], 
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    tags = models.JSONField(default=list)  # Requires PostgreSQL or Django 3.1+
    images = models.JSONField(default=list)  # List of image URLs
    is_best_seller = models.BooleanField(default=False)
    category_tree = models.CharField(max_length=1024)
    url = models.URLField(max_length=1024, blank=True, null=True)
    brand_name = models.CharField(max_length=255, blank=True, null=True)
    shipping_price = models.CharField(max_length=255, blank=True, null=True)
    shipping_price_currency = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
        
class Price(models.Model): 
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    first_variation_name = models.CharField(max_length=255, blank=True, null=True)
    second_variation_name = models.CharField(max_length=255, blank=True, null=True)
    first_variation_values = models.JSONField(default=list, blank=True, null=True)
    second_variation_values = models.JSONField(default=list, blank=True, null=True)
    has_variations = models.BooleanField(default=False, blank=False, null=False)
    has_combinations = models.BooleanField(default=False, blank=False, null=False)
    static_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    combination_prices = models.JSONField(default=list, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=False, null=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} - {self.created_at}"

class Currency(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    code = models.CharField(max_length=3, blank=False, null=False)
    symbol = models.CharField(max_length=3, blank=True, null=True, default="")
    in_row_symbol = models.CharField(max_length=3, blank=True, null=True, default="")

    def __str__(self):
        return self.name
    
class Package(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ScrapeProgress(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    progress = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.task_id} - {self.progress}%"