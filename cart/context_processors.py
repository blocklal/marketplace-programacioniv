def cart_processor(request):
    cart_count = 0
    
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            cart_count = cart.get_items_count()
        except:
            cart_count = 0
    
    return {
        'cart_total_items': cart_count
    }