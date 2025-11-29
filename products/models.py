from django.db import models
from accounts.models import Profile

# Create your models here.
#seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")

class Product(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    brand = models.CharField(blank=True, max_length=50, default="Genérico")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    on_stock = models.BooleanField(default=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
