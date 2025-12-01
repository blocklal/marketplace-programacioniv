from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, Category, SubCategory
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages

def product_list(request):
    products = Product.objects.all().order_by('-creation_time')
    categories = Category.objects.all()
    subcategories = []

    search_query = request.GET.get('search', '')
    selected_category_id = request.GET.get('category', '')
    selected_subcategory_ids = request.GET.getlist('subcategory') 
    brand = request.GET.get('brand', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    tipo_venta = request.GET.get('tipo_venta', '')
    solo_ofertas = request.GET.get('solo_ofertas', '')
    show_unavailable = request.GET.get('mostrar_agotados', 'false')

    if search_query:
        products = products.filter(name__icontains=search_query)

    if selected_category_id:
        try:
            selected_category = Category.objects.get(id=selected_category_id)
            subcategories = SubCategory.objects.filter(category=selected_category).order_by('name')
        except Category.DoesNotExist:
            selected_category_id = ''
            messages.warning(request, 'La categoría seleccionada no existe')
        
        if not selected_subcategory_ids:
            products = products.filter(category_id=selected_category_id)

    if selected_subcategory_ids:
        products = products.filter(subcategories__id__in=selected_subcategory_ids).distinct()

    if brand:
        products = products.filter(brand__icontains=brand)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if tipo_venta:
        products = products.filter(tipo_venta=tipo_venta)

    if solo_ofertas == 'true':
        products = products.filter(en_oferta=True, porcentaje_descuento__gt=0)

    if show_unavailable != 'true':
        products = products.filter(stock__gt=0)

    paginator = Paginator(products, 9) #Cantidad de productos por página
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'subcategories': subcategories,
        'search_query': search_query,
        'selected_category': selected_category_id,
        'selected_subcategory_ids': selected_subcategory_ids,
        'brand': brand,
        'min_price': min_price,
        'max_price': max_price,
        'tipo_venta': tipo_venta,
        'solo_ofertas': solo_ofertas,
        'mostrar_agotados': show_unavailable,
    }

    return render(request, 'products/product_list.html', context)

@login_required
def product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        
        subcategory_ids = request.POST.getlist('subcategories') 
        
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        brand = request.POST.get('brand')
        image = request.FILES.get('image')
        tipo_venta = request.POST.get('tipo_venta', 'venta')
        
        en_oferta = request.POST.get('en_oferta') == 'on'
        
        porcentaje_descuento = request.POST.get('porcentaje_descuento')
        if not porcentaje_descuento:
            porcentaje_descuento = 0
        
        if not price or price.strip() == '' or tipo_venta == 'intercambio':
            price = 0
        
        category = Category.objects.get(id=category_id)
        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            stock=stock,
            brand=brand,
            image=image,
            owner=request.user.profile,
            tipo_venta=tipo_venta,
            en_oferta=en_oferta,
            porcentaje_descuento=porcentaje_descuento
        )
        
        if subcategory_ids:
            subs = SubCategory.objects.filter(id__in=subcategory_ids)
            product.subcategories.set(subs)
        
        messages.success(request, f'Producto "{name}" creado exitosamente')
        return redirect('product_list')
    
    categories = Category.objects.all()
    return render(request, 'products/product_form.html', {'categories': categories})


@login_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.owner != request.user.profile:
        messages.error(request, 'No tienes permiso para editar este producto')
        return redirect('product_detail', product_id=product_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        subcategory_ids = request.POST.getlist('subcategories')
        
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        brand = request.POST.get('brand')
        on_stock = request.POST.get('on_stock') == 'on'
        tipo_venta = request.POST.get('tipo_venta', 'venta')
        
        en_oferta = request.POST.get('en_oferta') == 'on'
        
        porcentaje_descuento_str = request.POST.get('porcentaje_descuento')
        porcentaje_descuento = int(porcentaje_descuento_str) if porcentaje_descuento_str else 0
        
        if not price or price.strip() == '' or tipo_venta == 'intercambio':
            price = 0
        
        product.name = name
        product.category = Category.objects.get(id=category_id)
        product.description = description
        product.price = price
        product.stock = stock
        product.brand = brand
        product.on_stock = on_stock
        product.tipo_venta = tipo_venta
        product.en_oferta = en_oferta
        product.porcentaje_descuento = porcentaje_descuento
        
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        
        product.save()
        
        if subcategory_ids:
            subs = SubCategory.objects.filter(id__in=subcategory_ids)
            product.subcategories.set(subs) 
        else:
            product.subcategories.clear()
        
        messages.success(request, f'Producto "{name}" actualizado exitosamente')
        return redirect('product_detail', product_id=product.id)
    
    categories = Category.objects.all()
    if product.category:
        available_subcategories = SubCategory.objects.filter(category=product.category).order_by('name')
    else:
        available_subcategories = SubCategory.objects.none()
        
    return render(request, 'products/product_edit.html', {
        'product': product,
        'categories': categories,
        'subcategories': available_subcategories
    })

@login_required
def product_delete(request, product_id):
    """Eliminar un producto"""
    product = get_object_or_404(Product, id=product_id)
    
    if product.owner != request.user.profile:
        messages.error(request, 'No tienes permiso para eliminar este producto')
        return redirect('product_detail', product_id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado exitosamente')
        return redirect('my_products')
    
    context = {
        'product': product
    }
    return render(request, 'products/product_delete_confirm.html', context)

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

@login_required
def my_products(request):
    """Listar mis productos"""
    products = Product.objects.filter(owner=request.user.profile).order_by('-creation_time')
    
    context = {
        'products': products
    }
    return render(request, 'products/my_products.html', context)

def category_add(request):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para agregar categorías')
        return redirect('product_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        subcategories = request.POST.getlist('subcategories')

        category = Category.objects.create(
            name=name,
            description=description
        )

        for subcat_name in subcategories:
            if subcat_name.strip():
                SubCategory.objects.create(
                    name=subcat_name.strip(),
                    category=category
                )

        messages.success(request, f'Categoría "{name}" creada exitosamente')
        return redirect('category_list')
    
    return render(request, 'categories/category_form.html')


def category_list(request):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para ver las categorías')
        return redirect('product_list')
    categories = Category.objects.prefetch_related('subcategories').order_by('name')
    return render(request, 'categories/category_list.html', {'categories': categories})

def category_edit(request, category_id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para editar categorías')
        return redirect('product_list')
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        new_name = request.POST.get('name')
        if new_name is not None:
            category.name = new_name.strip() or category.name
            category.save()

        if action == 'delete_sub':
            sub_id = request.POST.get('sub_id')
            SubCategory.objects.filter(id=sub_id, category=category).delete()
            messages.success(request, 'Subcategoría eliminada')
            return redirect('category_edit', category_id=category.id)

        elif action == 'add_sub':
            sub_name = request.POST.get('new_sub_name', '').strip()
            if sub_name:
                exists = SubCategory.objects.filter(category=category, name__iexact=sub_name).exists()
                if exists:
                    messages.warning(request, 'La subcategoría ya existe en esta categoría')
                else:
                    SubCategory.objects.create(category=category, name=sub_name)
                    messages.success(request, f'Subcategoría "{sub_name}" agregada')
            else:
                messages.error(request, 'El nombre de la subcategoría no puede estar vacío')
            return redirect('category_edit', category_id=category.id)

        return redirect('category_edit', category_id=category.id)

    current_subs = SubCategory.objects.filter(category=category).order_by('name')

    return render(request, 'categories/category_edit.html', {
        'category': category,
        'current_subs': current_subs,
    })

def load_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    return JsonResponse(list(subcategories.values('id', 'name')), safe=False)