from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_favoritos, name='lista_favoritos'),
    path('agregar/<int:producto_id>/', views.agregar_favorito, name='agregar_favorito'),
    path('quitar/<int:producto_id>/', views.quitar_favorito, name='quitar_favorito'),
    path('toggle/<int:producto_id>/', views.toggle_favorito, name='toggle_favorito'),
]