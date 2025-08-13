import logging
import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from .cart import Cart

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def is_ajax(request):
    """Check if the request is an AJAX request."""
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def convert_decimals_to_float(data):
    """Recursively convert Decimal objects to float in data structures."""
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {key: convert_decimals_to_float(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_decimals_to_float(item) for item in data]
    return data

def safe_cart_operation(func):
    """Decorator to safely handle cart operations with error handling."""
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Cart operation error for user {request.user.id}: {str(e)}")
            if is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'message': f'Error processing cart: {str(e)}'
                }, status=500)
            request.session.pop('cart', None)
            messages.error(request, 'There was an error with your cart. It has been cleared.')
            return redirect('cart:cart_detail')
    return wrapper

@require_POST
@safe_cart_operation
def cart_add(request, product_id):
    """
    Add a product to the cart, supporting both AJAX and non-AJAX requests.
    """
    logger.info(f"Adding product {product_id} to cart for user {request.user.id}. Session: {request.session.session_key}")
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > product.stock:
            raise ValueError(f"Requested quantity ({quantity}) exceeds available stock ({product.stock})")
        cart.add(product=product, quantity=quantity, override_quantity=False)
        response_data = {
            'success': True,
            'cart_count': cart.get_total_items(),
            'message': f'{product.name} added to cart'
        }
        if is_ajax(request):
            return JsonResponse(response_data)
        messages.success(request, f'{product.name} added to cart')
        return redirect('cart:cart_detail')
    except ValueError as e:
        logger.warning(f"Invalid input for product {product_id} by user {request.user.id}: {str(e)}")
        if is_ajax(request):
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        messages.error(request, str(e))
        return redirect('products:product_detail', id=product.id, slug=product.slug)

@require_POST
@safe_cart_operation
def cart_remove(request, product_id):
    """
    Remove a product from the cart.
    """
    logger.info(f"Removing product {product_id} from cart for user {request.user.id}")
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product_id)
    response_data = {
        'success': True,
        'cart_count': cart.get_total_items(),
        'message': f'{product.name} removed from cart'
    }
    if is_ajax(request):
        return JsonResponse(response_data)
    messages.success(request, f'{product.name} removed from cart')
    return redirect('cart:cart_detail')

@require_POST
@safe_cart_operation
def cart_update(request, product_id):
    """
    Update the quantity of a product in the cart.
    """
    logger.info(f"Updating product {product_id} quantity for user {request.user.id}")
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity > product.stock:
            logger.warning(f"Invalid quantity {quantity} for product {product.id}. Stock: {product.stock}")
            if is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot update to {quantity} of {product.name}. Only {product.stock} in stock.'
                }, status=400)
            messages.error(request, f'Cannot update to {quantity} of {product.name}. Only {product.stock} in stock.')
            return redirect('cart:cart_detail')
        if quantity > 0:
            cart.add(product=product, quantity=quantity, override_quantity=True)
            message = f'{product.name} quantity updated'
        else:
            cart.remove(product_id)
            message = f'{product.name} removed from cart'
        response_data = {
            'success': True,
            'cart_count': cart.get_total_items(),
            'message': message
        }
        if is_ajax(request):
            return JsonResponse(response_data)
        messages.success(request, message)
        return redirect('cart:cart_detail')
    except ValueError as e:
        logger.warning(f"Invalid quantity for product {product_id}: {str(e)}")
        if is_ajax(request):
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        messages.error(request, str(e))
        return redirect('cart:cart_detail')

@safe_cart_operation
def cart_clear(request):
    """
    Clear all items from the cart.
    """
    logger.info(f"Clearing cart for user {request.user.id}. Session: {request.session.session_key}")
    cart = Cart(request)
    cart.clear()
    response_data = {
        'success': True,
        'cart_count': 0,
        'message': 'Cart cleared'
    }
    if is_ajax(request):
        return JsonResponse(response_data)
    messages.success(request, 'Cart cleared')
    return redirect('cart:cart_detail')

@safe_cart_operation
def cart_detail(request):
    """
    Display the cart contents, supporting both AJAX and non-AJAX requests.
    """
    logger.info(f"Displaying cart for user {request.user.id}. Session: {request.session.session_key}")
    cart = Cart(request)
    cart_items = cart.get_cart_data_for_json()  # Use get_cart_data_for_json for consistency
    total_price = float(cart.get_total_price() or 0)
    context = {
        'cart': cart_items,
        'cart_total_price': total_price,
    }
    if is_ajax(request):
        return JsonResponse(convert_decimals_to_float(context), encoder=DecimalEncoder)
    return render(request, 'cart/detail.html', context)