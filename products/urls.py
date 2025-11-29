from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('agregar/', views.product_add, name='product_add'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('categorias/agregar/', views.category_add, name='category_add'),
]