from django.contrib import admin
from .models import Order, OrderItem, Review

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'paid', 'created_at']
    list_filter = ['status', 'paid', 'created_at']
    search_fields = ['order_number', 'user__username']
    readonly_fields = ['order_number', 'subtotal', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'product_price', 'subtotal']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['autor', 'receptor', 'calificacion', 'fecha_creacion']
    list_filter = ['calificacion', 'fecha_creacion']
    search_fields = ['autor__username', 'receptor__username', 'comentario']
    readonly_fields = ['fecha_creacion']
    
    def has_add_permission(self, request):
        return False