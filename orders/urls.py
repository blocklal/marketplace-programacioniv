from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('create/', views.create_order, name='create_order'),
    path('mis-ordenes/', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/cancelar/', views.cancel_order, name='cancel_order'),
    
    # Vendedores
    path('ventas/', views.seller_orders, name='seller_orders'),
    path('ventas/<int:order_id>/', views.seller_order_detail, name='seller_order_detail'),
    path('ventas/<int:order_id>/actualizar/', views.update_order_status, name='update_order_status'),
]