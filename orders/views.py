from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Order, OrderItem, Review
from cart.models import Cart
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime


@login_required
def checkout(request):
    """Página de checkout"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.all():
        messages.error(request, 'Tu carrito está vacío')
        return redirect('cart_view')
    
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
    
    shipping_address = request.POST.get('shipping_address')
    shipping_city = request.POST.get('shipping_city')
    shipping_country = request.POST.get('shipping_country', 'Argentina')
    shipping_phone = request.POST.get('shipping_phone')
    payment_method = request.POST.get('payment_method')
    
    if not all([shipping_address, shipping_city, shipping_phone, payment_method]):
        messages.error(request, 'Por favor completa todos los campos')
        return redirect('checkout')
    
    subtotal = cart.get_total()
    shipping_cost = 0
    total = subtotal + shipping_cost
    
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
        paid=True,
        paid_at=timezone.now()
    )
    
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            product_name=cart_item.product.name,
            product_price=cart_item.product.price,
            quantity=cart_item.quantity,
            subtotal=cart_item.get_subtotal()
        )
        
        product = cart_item.product
        product.stock -= cart_item.quantity
        if product.stock == 0:
            product.on_stock = False
        product.save()
    
    cart.items.all().delete()
    
    messages.success(request, f'¡Orden #{order.order_number} creada exitosamente!')
    return redirect('order_detail', order_id=order.id)

@login_required
def order_list(request):

    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__seller'
    ).order_by('-created_at')
    
    for order in orders:
        for item in order.items.all():
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
    
    order_items = OrderItem.objects.filter(
        product__owner=seller_profile
    ).select_related('order', 'product').order_by('-order__created_at')
    
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
    
    if request.user == receptor:
        messages.error(request, 'No puedes dejarte una review a ti mismo.')
        return redirect('profile_view_user', username=username)
    
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
    
    review_existente = Review.objects.filter(autor=request.user, receptor=receptor).first()
    
    if request.method == 'POST':
        calificacion = request.POST.get('calificacion')
        comentario = request.POST.get('comentario', '')
        
        try:
            if review_existente:
                review_existente.calificacion = int(calificacion)
                review_existente.comentario = comentario
                review_existente.save()
                messages.success(request, 'Review actualizada exitosamente.')
            else:
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
    
    vendedores = User.objects.filter(
        sold_items__order__user=request.user,
        sold_items__order__status='delivered'
    ).exclude(
        id=request.user.id
    ).distinct()
    
    compradores = User.objects.filter(
        orders__items__seller=request.user,
        orders__status='delivered'
    ).exclude(
        id=request.user.id
    ).distinct()
    
    usuarios_transaccion = (vendedores | compradores).distinct()
    
    for usuario in usuarios_transaccion:
        usuario.mi_review = Review.objects.filter(
            autor=request.user,
            receptor=usuario
        ).first()
    
    context = {
        'usuarios': usuarios_transaccion,
    }
    return render(request, 'reviews/pendientes_review.html', context)

@login_required
def download_receipt_pdf(request, order_id):
    """Generar y descargar recibo en PDF"""
    order = get_object_or_404(Order, id=order_id)
    
    # Verificar que el usuario sea el comprador o vendedor
    is_buyer = order.user == request.user
    is_seller = OrderItem.objects.filter(
        order=order,
        product__owner=request.user.profile
    ).exists()
    
    if not (is_buyer or is_seller):
        messages.error(request, 'No tienes permiso para ver este recibo')
        return redirect('order_list')
    
    # Crear el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Contenedor para los elementos del PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C5AA0'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4A90E2'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # ENCABEZADO CON LOGO Y DATOS DE LA EMPRESA
    header_data = [
        [
            Paragraph('<font size=16 color="#2C5AA0"><b>🐱 Blue Shopping</b></font>', styles['Normal']),
            Paragraph('<font size=7>Calle falsa 123 | +54 9 12341234<br/>CUIT: 20-77777777-5 | www.blueshopping.com.ar</font>', 
                    ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=7))
        ]
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Línea separadora azul
    line_data = [['', '']]
    line_table = Table(line_data, colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#4A90E2')),  # Reducido de 3 a 2
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # TÍTULO
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,  # Reducido de 24 a 20
        textColor=colors.HexColor('#2C5AA0'),
        spaceAfter=20,  # Reducido de 30 a 20
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # DATOS DE LA ORDEN
    order_info_data = [
        ['Número de Orden:', f'#{order.order_number}'],
        ['Fecha:', order.created_at.strftime('%d/%m/%Y %H:%M')],
        ['Estado:', order.get_status_display()],
        ['Estado de Pago:', 'PAGADO' if order.paid else 'PENDIENTE'],
    ]
    
    order_info_table = Table(order_info_data, colWidths=[2*inch, 4.5*inch])
    order_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C5AA0')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(order_info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # DATOS DEL CLIENTE
    elements.append(Paragraph('INFORMACIÓN DEL CLIENTE', heading_style))
    
    customer_data = [
        ['Cliente:', order.user.username],
        ['Email:', order.user.email],
        ['Teléfono:', order.shipping_phone],
        ['Dirección de Envío:', f'{order.shipping_address}, {order.shipping_city}, {order.shipping_country}'],
    ]
    
    customer_table = Table(customer_data, colWidths=[2*inch, 4.5*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C5AA0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # TABLA DE PRODUCTOS
    elements.append(Paragraph('DETALLE DE PRODUCTOS', heading_style))
    
    # Encabezados de la tabla
    products_data = [
        ['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']
    ]
    
    # Agregar productos
    for item in order.items.all():
        products_data.append([
            Paragraph(item.product_name, normal_style),
            str(item.quantity),
            f'${item.product_price}',
            f'${item.subtotal}'
        ])
    
    products_table = Table(products_data, colWidths=[3*inch, 1*inch, 1.25*inch, 1.25*inch])
    products_table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Contenido
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2C5AA0')),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(products_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # TOTALES
    totals_data = [
        ['Subtotal:', f'${order.subtotal}'],
        ['Envío:', 'GRATIS' if order.shipping_cost == 0 else f'${order.shipping_cost}'],
        ['', ''],  # Espacio
        ['TOTAL:', f'${order.total}'],
    ]
    
    totals_table = Table(totals_data, colWidths=[4.75*inch, 1.75*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 2), 'Helvetica'),
        ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        ('FONTSIZE', (0, 3), (-1, 3), 14),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#2C5AA0')),
        ('LINEABOVE', (0, 3), (-1, 3), 2, colors.HexColor('#4A90E2')),
        ('TOPPADDING', (0, 3), (-1, 3), 10),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # MÉTODO DE PAGO
    payment_data = [
        ['Método de Pago:', order.get_payment_method_display()],
    ]
    
    payment_table = Table(payment_data, colWidths=[2*inch, 4.5*inch])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C5AA0')),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # PIE DE PÁGINA CON TÉRMINOS
    terms_style = ParagraphStyle(
        'Terms',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER,
        leading=10
    )
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Línea separadora
    line_data2 = [['', '']]
    line_table2 = Table(line_data2, colWidths=[6.5*inch])
    line_table2.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.lightgrey),
    ]))
    elements.append(line_table2)
    elements.append(Spacer(1, 0.1*inch))
    
    terms_text = """
    <b>TÉRMINOS Y CONDICIONES</b><br/>
    Este recibo es un comprobante de compra emitido por Blue Shopping. 
    Conserve este documento para futuras consultas o reclamos.<br/>
    Para soporte o consultas, contacte a: +54 9 12341234 o info@blueshopping.com.ar<br/>
    Gracias por su compra. 🐱
    """
    elements.append(Paragraph(terms_text, terms_style))
    
    # Generar el PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_orden_{order.order_number}.pdf"'
    response.write(pdf)
    
    return response