from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created']
        unique_together = ['product', 'user']  # One review per user per product
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['product', 'active']),
        ]
    
    def __str__(self):
        return f'Review by {self.user.username} for {self.product.name}'
    
    @property
    def rating_range(self):
        """Return a range for template star rendering"""
        return range(1, 6)
    
    @property
    def filled_stars(self):
        """Return range of filled stars"""
        return range(1, self.rating + 1)
    
    @property
    def empty_stars(self):
        """Return range of empty stars"""
        return range(self.rating + 1, 6)


class ReviewHelpful(models.Model):
    """Track which users found reviews helpful"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f'{self.user.username} found review {self.review.id} helpful'