from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User

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
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    context = {
        'profile_user': user,
        'profile': user.profile
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