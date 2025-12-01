from django.urls import path, include
from . import views

urlpatterns = [
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('perfil/', views.profile_view, name='profile_view'),
    path('perfil/editar/', views.profile_edit, name='profile_edit'),
    path('perfil/<str:username>/', views.profile_view, name='profile_view_user'),
    path('social/', include('allauth.urls')),
    path('ingresarcontraseña', views.set_password, name="set_password" ),
    path('change-username/', views.change_username, name='change_username'),
    path('change-password/', views.change_password, name='change_password'),
]