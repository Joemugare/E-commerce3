# products/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/%Y/%m/%d/', blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product_list_by_category', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if not self.name:
            raise ValidationError("Category name is required.")
        super().clean()

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, blank=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Added
    available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.id, self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if not self.name:
            raise ValidationError("Product name is required.")
        if self.price < 0:
            raise ValidationError("Price cannot be negative.")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative.")
        if self.discount_price and self.discount_price < 0:
            raise ValidationError("Discount price cannot be negative.")
        super().clean()

    @property
    def is_in_stock(self):
        return self.stock > 0

    def get_average_rating(self):
        reviews = self.reviews.filter(active=True)
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0

    def get_review_count(self):
        return self.reviews.filter(active=True).count()

    def get_discount_percentage(self):  # Added
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0