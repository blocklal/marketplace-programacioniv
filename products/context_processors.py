from products.models import Category

def categories_processor(request):
    """Hace que las categorías estén disponibles en todos los templates"""
    return {
        'categories': Category.objects.all()
    }