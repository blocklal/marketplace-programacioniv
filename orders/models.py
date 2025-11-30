from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta de Débito'),
        ('paypal', 'PayPal'),
        ('transfer', 'Transferencia Bancaria'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Información del pedido
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Información de envío
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    
    # Pago
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    paid = models.BooleanField(default=False)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Orden #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generar número de orden único
            import random
            import string
            self.order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sold_items', null=True, blank=True)  # NUEVO
    
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.seller_id and self.product and self.product.owner:
            self.seller = self.product.owner.user
        super().save(*args, **kwargs)

    def tiene_review_de_comprador(self, usuario):
        """Verifica si el comprador ya dejó review para este item"""
        return self.reviews.filter(autor=usuario, tipo='vendedor').exists()
    
    def get_review_de_comprador(self, usuario):
        """Obtiene la review del comprador si existe"""
        return self.reviews.filter(autor=usuario, tipo='vendedor').first()
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name} (Orden #{self.order.order_number})"
    

class Review(models.Model):
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_escritas')
    receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_recibidas')
    
    calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Calificación de 1 a 5 estrellas"
    )
    comentario = models.TextField(max_length=1000)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['autor', 'receptor']  # Una review por cada par de usuarios
        ordering = ['-fecha_creacion']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        indexes = [
            models.Index(fields=['receptor', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Review de {self.autor.username} para {self.receptor.username} ({self.calificacion}⭐)"
    
    def clean(self):
        """Validaciones personalizadas"""
        # No puedes dejarte una review a ti mismo
        if self.autor == self.receptor:
            raise ValidationError('No puedes dejarte una review a ti mismo.')
        
        # Verificar que haya al menos una transacción entre ellos
        if not self.tienen_transaccion():
            raise ValidationError('Debes tener al menos una compra/venta con este usuario para dejar una review.')
    
    def tienen_transaccion(self):
        """Verifica si hay al menos una transacción entre autor y receptor"""
        from orders.models import Order, OrderItem
        
        # Caso 1: Autor compró algo al receptor
        compro_a = OrderItem.objects.filter(
            order__user=self.autor,
            seller=self.receptor,
            order__status='delivered'
        ).exists()
        
        # Caso 2: Autor vendió algo al receptor
        vendio_a = OrderItem.objects.filter(
            order__user=self.receptor,
            seller=self.autor,
            order__status='delivered'
        ).exists()
        
        return compro_a or vendio_a
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)