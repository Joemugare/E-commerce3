from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from .cart import Cart


def cart_detail(request):
    """Display cart contents"""
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    """Add product to cart"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    cart.add(product=product, quantity=quantity, override_quantity=False)
    
    if request.is_ajax():
        return JsonResponse({
            'success': True,
            'cart_total_items': len(cart),
            'message': f'{product.name} added to cart'
        })
    
    messages.success(request, f'{product.name} added to cart')
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    """Remove product from cart"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    
    if request.is_ajax():
        return JsonResponse({
            'success': True,
            'cart_total_items': len(cart),
            'message': f'{product.name} removed from cart'
        })
    
    messages.success(request, f'{product.name} removed from cart')
    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, product_id):
    """Update product quantity in cart"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart.add(product=product, quantity=quantity, override_quantity=True)
        message = f'{product.name} quantity updated'
    else:
        cart.remove(product)
        message = f'{product.name} removed from cart'
    
    if request.is_ajax():
        return JsonResponse({
            'success': True,
            'cart_total_items': len(cart),
            'message': message
        })
    
    messages.success(request, message)
    return redirect('cart:cart_detail')


def cart_clear(request):
    """Clear all items from cart"""
    cart = Cart(request)
    cart.clear()
    
    if request.is_ajax():
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared'
        })
    
    messages.success(request, 'Cart cleared')
    return redirect('cart:cart_detail')