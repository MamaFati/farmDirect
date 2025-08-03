from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

# Create your models here.
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name