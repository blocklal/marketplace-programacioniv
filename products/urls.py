from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('agregar/', views.product_add, name='product_add'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('<int:product_id>/editar/', views.product_edit, name='product_edit'),
    path('<int:product_id>/eliminar/', views.product_delete, name='product_delete'),
    path('mis-productos/', views.my_products, name='my_products'),
    path('categorias/agregar/', views.category_add, name='category_add'),
]