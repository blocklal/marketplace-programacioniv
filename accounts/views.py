# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User
from orders.models import Review, OrderItem
from django.db.models import Avg
from django.contrib import messages
from products.models import Product, Category
from django.db.models import Sum, Q, Count


def home(request):
    # Productos más vendidos (top 8)
    productos_mas_vendidos = Product.objects.filter(
        orderitem__order__status='delivered'
    ).annotate(
        total_vendidos=Sum('orderitem__quantity')
    ).filter(
        total_vendidos__isnull=False
    ).order_by('-total_vendidos')[:8]
    
    # Si no hay productos vendidos, mostrar los más recientes
    if not productos_mas_vendidos.exists():
        productos_mas_vendidos = Product.objects.filter(
            Q(on_stock=True) & Q(stock__gt=0)
        ).order_by('-creation_time')[:8]
        # Agregar total_vendidos = 0 manualmente
        for producto in productos_mas_vendidos:
            producto.total_vendidos = 0
    
    # Productos en oferta (top 8)
    productos_en_oferta = Product.objects.filter(
        en_oferta=True,
        on_stock=True,
        stock__gt=0
    ).order_by('-porcentaje_descuento')[:8]
    
    # Categorías
    categories = Category.objects.all()
    
    context = {
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_en_oferta': productos_en_oferta,
        'categories': categories,
    }
    
    return render(request, 'home.html', context)

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    
    else:
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}! Tu cuenta ha sido creada')
            return redirect('product_list')
        
        return render(request, 'signup.html', {'form': form})
        
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'],
            password=request.POST['password'])
        if user is None:
            messages.error(request, 'El usuario o la contraseña son incorrectos')
            return render(request, 'signin.html', {'form': AuthenticationForm()})
        else:
            login(request, user)
            messages.success(request, f'¡Bienvenido de nuevo {user.username}!')
            return redirect('product_list')

def signout(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Has cerrado sesión exitosamente')
        return redirect('product_list')
    
    return render(request, 'logout.html')

@login_required
def profile_view(request, username=None):
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)
    
    profile = profile_user.profile
    
    reviews = Review.objects.filter(receptor=profile_user).select_related('autor')
    
    promedio = reviews.aggregate(Avg('calificacion'))['calificacion__avg']
    promedio = round(promedio, 1) if promedio else 0
    
    puede_dejar_review = False
    mi_review = None
    
    if request.user.is_authenticated and request.user != profile_user:
        compro_a = OrderItem.objects.filter(
            order__user=request.user,
            seller=profile_user,
            order__status='delivered'
        ).exists()
        
        vendio_a = OrderItem.objects.filter(
            order__user=profile_user,
            seller=request.user,
            order__status='delivered'
        ).exists()
        
        puede_dejar_review = compro_a or vendio_a
        mi_review = Review.objects.filter(autor=request.user, receptor=profile_user).first()
    
    context = {
        'profile_user': profile_user,
        'profile': profile,
        'reviews': reviews,
        'promedio': promedio,
        'total_reviews': reviews.count(),
        'puede_dejar_review': puede_dejar_review,
        'mi_review': mi_review,
    }
    return render(request, 'profiles/profile.html', context)

@login_required
def profile_edit(request):
    profile = request.user.profile
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        
        messages.success(request, 'Perfil actualizado exitosamente')
        return redirect('profile_view')
    
    context = {
        'profile': profile
    }
    return render(request, 'profiles/profile_edit.html', context)