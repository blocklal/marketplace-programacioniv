from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Category

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