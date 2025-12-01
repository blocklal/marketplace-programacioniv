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

# Create your views here.



def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    
    else:
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
        
        # Si el form no es válido, se renderea con los errores
        return render(request, 'signup.html', {'form': form})
        
def signin(request):

    if request.method == 'GET':
        return render(request, 'signin.html',
            {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'],
            password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html',
            {'form': AuthenticationForm(),
            'error': 'El usuario o la contraseña son incorrectos'})
        else:
            login(request, user)
            return redirect('product_list')

def signout(request):
    logout(request)
    return redirect('signin')

def signout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('product_list')
    
    # GET - mostrar confirmación
    return render(request, 'logout.html')

@login_required
def profile_view(request, username=None):
    # Si no hay username, mostrar el perfil del usuario actual
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)
    
    profile = profile_user.profile
    
    # Reviews recibidas (simplificado: una review por persona)
    reviews = Review.objects.filter(receptor=profile_user).select_related('autor')
    
    # Calcular promedio general
    promedio = reviews.aggregate(Avg('calificacion'))['calificacion__avg']
    promedio = round(promedio, 1) if promedio else 0
    
    # Verificar si el usuario actual puede dejar review
    puede_dejar_review = False
    mi_review = None
    
    if request.user.is_authenticated and request.user != profile_user:
        # Verificar si hay transacción completada entre ellos
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
        # Actualizar datos del User
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Actualizar datos del Profile
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        
        # Manejar imagen
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        
        return redirect('profile_view')
    
    context = {
        'profile': profile
    }
    return render(request, 'profiles/profile_edit.html', context)