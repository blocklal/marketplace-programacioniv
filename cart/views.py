from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Cart, CartItem
from products.models import Product

@login_required
def cart_view(request):
    """Ver el carrito"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart
    }
    return render(request, 'cart/cart.html', context)

@login_required
def cart_add(request, product_id):
    """Agregar producto al carrito"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Verificar si el producto ya está en el carrito
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        message = f'Se agregó otra unidad de {product.name} al carrito'
    else:
        message = f'{product.name} agregado al carrito'
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart.get_items_count()
        })
    
    # Si no, comportamiento normal
    messages.success(request, message)
    return redirect('cart_view')

@login_required
def cart_update(request, item_id):
    """Actualizar cantidad de un item"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            if quantity <= cart_item.product.stock:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Cantidad actualizada')
            else:
                messages.error(request, f'Solo hay {cart_item.product.stock} unidades disponibles')
        else:
            cart_item.delete()
            messages.success(request, 'Producto eliminado del carrito')
    
    return redirect('cart_view')

@login_required
def cart_remove(request, item_id):
    """Eliminar item del carrito"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} eliminado del carrito')
    return redirect('cart_view')

@login_required
def cart_clear(request):
    """Vaciar el carrito"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, 'Carrito vaciado')
    return redirect('cart_view')