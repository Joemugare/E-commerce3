# cart/context_processors.py
from .models import Cart

def cart(request):
    """Add cart to template context"""
    cart_obj = None
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
    elif 'cart_id' in request.session:
        try:
            cart_obj = Cart.objects.get(session_key=request.session['cart_id'])
        except Cart.DoesNotExist:
            pass
    
    return {'cart': cart_obj}

# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from .models import Cart, CartItem

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if 'cart_id' not in request.session:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.session_key = cart.id
            cart.save()
        else:
            try:
                cart = Cart.objects.get(session_key=request.session['cart_id'])
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.session_key = cart.id
                cart.save()
    return cart

def cart_detail(request):
    """Display cart contents"""
    cart = get_or_create_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})

@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check stock
    if product.stock < quantity:
        messages.error(request, f'Only {product.stock} items available.')
        return redirect('products:product_detail', slug=product.slug)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.get_total_items(),
            'cart_total_price': str(cart.get_total_price())
        })
    
    return redirect('cart:cart_detail')

@require_POST
def update_cart(request, item_id):
    """Update cart item quantity"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        if cart_item.product.stock >= quantity:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated.')
        else:
            messages.error(request, f'Only {cart_item.product.stock} items available.')
    else:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    
    return redirect('cart:cart_detail')

def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.success(request, f'{cart_item.product.name} removed from cart.')
    return redirect('cart:cart_detail')