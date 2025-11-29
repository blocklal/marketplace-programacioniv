from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Favorito
from products.models import Product

@login_required
@require_POST
def agregar_favorito(request, producto_id):
    producto = get_object_or_404(Product, id=producto_id)
    favorito, created = Favorito.objects.get_or_create(
        usuario=request.user,
        producto=producto
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'created': created,
            'message': 'Agregado a favoritos' if created else 'Ya estaba en favoritos'
        })
    
    return redirect('detalle_producto', producto_id=producto_id)


@login_required
@require_POST
def quitar_favorito(request, producto_id):
    producto = get_object_or_404(Product, id=producto_id)
    deleted = Favorito.objects.filter(
        usuario=request.user,
        producto=producto
    ).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'deleted': deleted[0] > 0,
            'message': 'Eliminado de favoritos'
        })
    
    return redirect('lista_favoritos')


@login_required
@require_POST
def toggle_favorito(request, producto_id):
    """Vista para agregar o quitar con un solo botón"""
    producto = get_object_or_404(Product, id=producto_id)
    favorito = Favorito.objects.filter(usuario=request.user, producto=producto)
    
    if favorito.exists():
        favorito.delete()
        es_favorito = False
        mensaje = 'Eliminado de favoritos'
    else:
        Favorito.objects.create(usuario=request.user, producto=producto)
        es_favorito = True
        mensaje = 'Agregado a favoritos'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'es_favorito': es_favorito,
            'message': mensaje
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def lista_favoritos(request):
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('producto')
    
    context = {
        'favoritos': favoritos,
        'total_favoritos': favoritos.count()
    }
    return render(request, 'favoritos/lista_favoritos.html', context)
