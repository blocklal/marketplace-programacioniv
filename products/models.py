from django.db import models
from accounts.models import Profile
from decimal import Decimal

# Create your models here.
#seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")

class Product(models.Model):
    TIPO_VENTA_CHOICES = [
        ('venta', 'Solo Venta'),
        ('intercambio', 'Solo Intercambio'),
        ('ambos', 'Venta o Intercambio'),
    ]
    
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    subcategories = models.ManyToManyField('SubCategory', blank=True, related_name='products')
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)
    brand = models.CharField(blank=True, max_length=50, default="Genérico")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    on_stock = models.BooleanField(default=True)
    tipo_venta = models.CharField(max_length=20, choices=TIPO_VENTA_CHOICES, default='venta')
    
    # NUEVOS CAMPOS DE OFERTA
    en_oferta = models.BooleanField(default=False, verbose_name="En oferta")
    porcentaje_descuento = models.PositiveIntegerField(default=0, verbose_name="% de descuento", 
                                                        help_text="Descuento del 0 al 100%")
    
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def acepta_venta(self):
        return self.tipo_venta in ['venta', 'ambos']
    
    def acepta_intercambio(self):
        return self.tipo_venta in ['intercambio', 'ambos']
    
    def get_precio_oferta(self):
        if self.en_oferta and self.porcentaje_descuento > 0:
            descuento = self.price * (Decimal(self.porcentaje_descuento) / Decimal(100))
            return self.price - descuento
        return self.price

    def get_ahorro(self):
        """Calcula cuánto se ahorra con la oferta"""
        if self.en_oferta and self.porcentaje_descuento > 0:
            return self.price * (Decimal(self.porcentaje_descuento) / Decimal(100))
        return Decimal(0)
    
class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class SubCategory(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"