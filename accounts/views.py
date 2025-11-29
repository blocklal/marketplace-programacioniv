from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User
from orders.models import Review
from django.db.models import Avg

# Create your views here.



def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})

    else:
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.email = form.cleaned_data['email']
                user.save()
                login(request, user)


                return redirect('product_list')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': CustomUserCreationForm(),
                    'error': 'El usuario ya existe'
                })
        else:
            return render(request, 'signup.html', {
                'form': form,
                'error': 'Datos inválidos'
            })
        
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

@login_required
def profile_view(request, username=None):
    # Si no hay username, mostrar el perfil del usuario actual
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)
    
    profile = profile_user.profile
    
    # Reviews
    reviews_vendedor = Review.objects.filter(receptor=profile_user, tipo='vendedor').select_related('autor', 'order_item')
    reviews_comprador = Review.objects.filter(receptor=profile_user, tipo='comprador').select_related('autor', 'order_item')
    
    # Calcular promedios
    promedio_vendedor = reviews_vendedor.aggregate(Avg('calificacion'))['calificacion__avg']
    promedio_comprador = reviews_comprador.aggregate(Avg('calificacion'))['calificacion__avg']
    
    promedio_vendedor = round(promedio_vendedor, 1) if promedio_vendedor else 0
    promedio_comprador = round(promedio_comprador, 1) if promedio_comprador else 0
    
    context = {
        'profile_user': profile_user,
        'profile': profile,
        'reviews_vendedor': reviews_vendedor,
        'reviews_comprador': reviews_comprador,
        'promedio_vendedor': promedio_vendedor,
        'promedio_comprador': promedio_comprador,
        'total_reviews_vendedor': reviews_vendedor.count(),
        'total_reviews_comprador': reviews_comprador.count(),
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