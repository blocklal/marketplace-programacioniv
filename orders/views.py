from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Order, OrderItem, Review
from cart.models import Cart
from django.contrib.auth.models import User

@login_required
def checkout(request):
    """Página de checkout"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.all():
        messages.error(request, 'Tu carrito está vacío')
        return redirect('cart_view')
    
    # Usar datos del perfil si existen
    profile = request.user.profile
    
    context = {
        'cart': cart,
        'profile': profile
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def create_order(request):
    """Crear la orden desde el carrito"""
    if request.method != 'POST':
        return redirect('checkout')
    
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.all():
        messages.error(request, 'Tu carrito está vacío')
        return redirect('cart_view')
    
    # Obtener datos del formulario
    shipping_address = request.POST.get('shipping_address')
    shipping_city = request.POST.get('shipping_city')
    shipping_country = request.POST.get('shipping_country', 'Argentina')
    shipping_phone = request.POST.get('shipping_phone')
    payment_method = request.POST.get('payment_method')
    
    # Validaciones
    if not all([shipping_address, shipping_city, shipping_phone, payment_method]):
        messages.error(request, 'Por favor completa todos los campos')
        return redirect('checkout')
    
    # Calcular totales
    subtotal = cart.get_total()
    shipping_cost = 0  # Gratis por ahora
    total = subtotal + shipping_cost
    
    # Crear la orden
    order = Order.objects.create(
        user=request.user,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        shipping_address=shipping_address,
        shipping_city=shipping_city,
        shipping_country=shipping_country,
        shipping_phone=shipping_phone,
        payment_method=payment_method,
        paid=True,  # Simulamos que está pagado
        paid_at=timezone.now()
    )
    
    # Crear los items de la orden
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            product_name=cart_item.product.name,
            product_price=cart_item.product.price,
            quantity=cart_item.quantity,
            subtotal=cart_item.get_subtotal()
        )
        
        # Reducir stock del producto
        product = cart_item.product
        product.stock -= cart_item.quantity
        if product.stock == 0:
            product.on_stock = False
        product.save()
    
    # Vaciar el carrito
    cart.items.all().delete()
    
    messages.success(request, f'¡Orden #{order.order_number} creada exitosamente!')
    return redirect('order_detail', order_id=order.id)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__seller'  # Eliminar 'items__reviews' porque ya no existe esa relación
    ).order_by('-created_at')
    
    # Agregar la review del usuario para cada vendedor
    for order in orders:
        for item in order.items.all():
            # Buscar si el usuario ya dejó review a este vendedor
            item.user_review = Review.objects.filter(
                autor=request.user,
                receptor=item.seller
            ).first()
    
    context = {
        'orders': orders
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """Ver detalle de una orden"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def cancel_order(request, order_id):
    """Cancelar una orden"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['pending', 'processing']:
        order.status = 'cancelled'
        order.save()
        
        # Devolver stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.on_stock = True
            product.save()
        
        messages.success(request, 'Orden cancelada exitosamente')
    else:
        messages.error(request, 'No se puede cancelar esta orden')
    
    return redirect('order_detail', order_id=order.id)

@login_required
def seller_orders(request):
    """Ver pedidos de productos del vendedor"""
    seller_profile = request.user.profile
    
    # Buscar OrderItems que contengan productos del vendedor
    order_items = OrderItem.objects.filter(
        product__owner=seller_profile
    ).select_related('order', 'product').order_by('-order__created_at')
    
    # Agrupar por orden
    orders_dict = {}
    for item in order_items:
        order = item.order
        if order.id not in orders_dict:
            orders_dict[order.id] = {
                'order': order,
                'items': [],
                'seller_total': 0
            }
        orders_dict[order.id]['items'].append(item)
        orders_dict[order.id]['seller_total'] += item.subtotal
    
    orders = list(orders_dict.values())
    
    # Calcular estadísticas
    total_orders = len(orders)
    pending_count = sum(1 for o in orders if o['order'].status == 'pending')
    processing_count = sum(1 for o in orders if o['order'].status == 'processing')
    delivered_count = sum(1 for o in orders if o['order'].status == 'delivered')
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'delivered_count': delivered_count,
    }
    return render(request, 'orders/seller_orders.html', context)

@login_required
def seller_order_detail(request, order_id):
    """Ver detalle de un pedido como vendedor"""
    order = get_object_or_404(Order, id=order_id)
    seller_profile = request.user.profile
    
    # Verificar que el vendedor tenga productos en esta orden
    seller_items = OrderItem.objects.filter(
        order=order,
        product__owner=seller_profile
    )
    
    if not seller_items.exists():
        messages.error(request, 'No tienes productos en esta orden')
        return redirect('seller_orders')
    
    seller_total = sum(item.subtotal for item in seller_items)
    
    context = {
        'order': order,
        'seller_items': seller_items,
        'seller_total': seller_total
    }
    return render(request, 'orders/seller_order_detail.html', context)

@login_required
def update_order_status(request, order_id):
    """Actualizar el estado de una orden (solo vendedores)"""
    if request.method != 'POST':
        return redirect('seller_orders')
    
    order = get_object_or_404(Order, id=order_id)
    seller_profile = request.user.profile
    
    # Verificar que el vendedor tenga productos en esta orden
    seller_items = OrderItem.objects.filter(
        order=order,
        product__owner=seller_profile
    )
    
    if not seller_items.exists():
        messages.error(request, 'No tienes permisos para modificar esta orden')
        return redirect('seller_orders')
    
    new_status = request.POST.get('status')
    
    if new_status in dict(Order.STATUS_CHOICES).keys():
        order.status = new_status
        order.save()
        messages.success(request, f'Estado actualizado a {order.get_status_display()}')
    else:
        messages.error(request, 'Estado inválido')
    
    return redirect('seller_order_detail', order_id=order.id)


@login_required
def crear_review(request, username):
    """Crear o editar review para un usuario"""
    receptor = get_object_or_404(User, username=username)
    
    # No puedes dejarte review a ti mismo
    if request.user == receptor:
        messages.error(request, 'No puedes dejarte una review a ti mismo.')
        return redirect('profile_view_user', username=username)
    
    # Verificar que haya transacción
    compro_a = OrderItem.objects.filter(
        order__user=request.user,
        seller=receptor,
        order__status='delivered'
    ).exists()
    
    vendio_a = OrderItem.objects.filter(
        order__user=receptor,
        seller=request.user,
        order__status='delivered'
    ).exists()
    
    if not (compro_a or vendio_a):
        messages.error(request, 'Debes tener al menos una compra/venta completada con este usuario para dejar una review.')
        return redirect('profile_view_user', username=username)
    
    # Verificar si ya existe una review
    review_existente = Review.objects.filter(autor=request.user, receptor=receptor).first()
    
    if request.method == 'POST':
        calificacion = request.POST.get('calificacion')
        comentario = request.POST.get('comentario', '')
        
        try:
            if review_existente:
                # Actualizar review existente
                review_existente.calificacion = int(calificacion)
                review_existente.comentario = comentario
                review_existente.save()
                messages.success(request, 'Review actualizada exitosamente.')
            else:
                # Crear nueva review
                Review.objects.create(
                    autor=request.user,
                    receptor=receptor,
                    calificacion=int(calificacion),
                    comentario=comentario
                )
                messages.success(request, 'Review enviada exitosamente.')
            
            return redirect('profile_view_user', username=receptor.username)
        except Exception as e:
            messages.error(request, f'Error al guardar review: {str(e)}')
    
    context = {
        'receptor': receptor,
        'review_existente': review_existente,
        'compro_a': compro_a,
        'vendio_a': vendio_a,
    }
    return render(request, 'reviews/crear_review.html', context)


@login_required
def mis_reviews_pendientes(request):
    """Lista de usuarios con los que puedes dejar review"""
    from django.db.models import Q
    
    # Usuarios a los que les compraste (vendedores)
    vendedores = User.objects.filter(
        sold_items__order__user=request.user,
        sold_items__order__status='delivered'
    ).exclude(
        id=request.user.id
    ).distinct()
    
    # Usuarios que te compraron (compradores)
    compradores = User.objects.filter(
        orders__items__seller=request.user,
        orders__status='delivered'
    ).exclude(
        id=request.user.id
    ).distinct()
    
    # Combinar ambos
    usuarios_transaccion = (vendedores | compradores).distinct()
    
    # Agregar si ya tienen review
    for usuario in usuarios_transaccion:
        usuario.mi_review = Review.objects.filter(
            autor=request.user,
            receptor=usuario
        ).first()
    
    context = {
        'usuarios': usuarios_transaccion,
    }
    return render(request, 'reviews/pendientes_review.html', context)