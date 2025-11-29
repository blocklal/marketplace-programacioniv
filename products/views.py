from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from django.contrib import messages

# Create your views here.

def product_list(request):
    products = Product.objects.filter(on_stock=True)
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    min_price = request.GET.get('min_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    
    max_price = request.GET.get('max_price', '')
    if max_price:
        products = products.filter(price__lte=max_price)
    

    brand = request.GET.get('brand', '')
    if brand:
        products = products.filter(brand__icontains=brand)
    
    products = products.order_by('-creation_time')
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'brand': brand,
    }
    return render(request, 'products/product_list.html', context)

@login_required
def product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        brand = request.POST.get('brand')
        image = request.FILES.get('image')
        owner=request.user
        
        category = Category.objects.get(id=category_id)
        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            stock=stock,
            brand=brand,
            image=image,
            owner=request.user.profile
        )
        
        return redirect('product_list')
    
    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_edit(request, product_id):
    """Editar un producto"""
    product = get_object_or_404(Product, id=product_id)
    
    # Verificar que el usuario sea el dueño
    if product.owner != request.user.profile:
        messages.error(request, 'No tienes permiso para editar este producto')
        return redirect('product_detail', product_id=product_id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        brand = request.POST.get('brand')
        on_stock = request.POST.get('on_stock') == 'on'
        
        # Actualizar producto
        product.name = name
        product.category = Category.objects.get(id=category_id)
        product.description = description
        product.price = price
        product.stock = stock
        product.brand = brand
        product.on_stock = on_stock
        
        # Actualizar imagen si se subió una nueva
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        
        product.save()
        
        messages.success(request, 'Producto actualizado exitosamente')
        return redirect('product_detail', product_id=product.id)
    
    # GET request - mostrar formulario
    categories = Category.objects.all()
    context = {
        'product': product,
        'categories': categories
    }
    return render(request, 'products/product_edit.html', context)

@login_required
def product_delete(request, product_id):
    """Eliminar un producto"""
    product = get_object_or_404(Product, id=product_id)
    
    # Verificar que el usuario sea el dueño
    if product.owner != request.user.profile:
        messages.error(request, 'No tienes permiso para eliminar este producto')
        return redirect('product_detail', product_id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado exitosamente')
        return redirect('profile_view')
    
    # Si no es POST, mostrar confirmación
    context = {
        'product': product
    }
    return render(request, 'products/product_delete_confirm.html', context)

@login_required
def my_products(request):
    """Listar mis productos"""
    products = Product.objects.filter(owner=request.user.profile).order_by('-creation_time')
    
    context = {
        'products': products
    }
    return render(request, 'products/my_products.html', context)


def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        Category.objects.create(
            name=name,
            description=description
        )
        
        return redirect('product_add')
    
    return render(request, 'products/category_form.html')

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    related_products = Product.objects.filter(
        category=product.category, 
        on_stock=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'products/product_detail.html', context)