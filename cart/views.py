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
    """Custom JSON encoder to handle Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def convert_decimals_to_float(data):
    """Recursively convert Decimal objects to float in data structures"""
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {key: convert_decimals_to_float(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_decimals_to_float(item) for item in data]
    return data

def safe_cart_operation(func):
    """Decorator to safely handle cart operations"""
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Cart operation error: {str(e)}")
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
    logger.info(f"Adding product {product_id} to cart. Session ID: {request.session.session_key}")
    try:
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id, available=True)
        quantity = request.POST.get('quantity', '1')
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if quantity > product.stock:
                raise ValueError(f"Requested quantity ({quantity}) exceeds available stock ({product.stock})")
        except ValueError as e:
            logger.warning(f"Invalid quantity for product {product.id}: {str(e)}")
            if is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
            messages.error(request, str(e))
            return redirect('products:product_detail', id=product.id, slug=product.slug)
        cart.add(product=product, quantity=quantity, override_quantity=False)
        response_data = {
            'success': True,
            'cart_count': int(cart.get_total_items()),
            'message': f'{product.name} added to cart'
        }
        if is_ajax(request):
            return JsonResponse(response_data)
        messages.success(request, f'{product.name} added to cart')
        return redirect('cart:cart_detail')
    except Exception as e:
        logger.error(f"Error adding product {product_id}: {str(e)}")
        if is_ajax(request):
            return JsonResponse({
                'success': False,
                'message': f'Error adding to cart: {str(e)}'
            }, status=500)
        messages.error(request, f'Error adding to cart: {str(e)}')
        return redirect('products:product_detail', id=product_id, slug=Product.objects.get(id=product_id).slug)

@require_POST
@safe_cart_operation
def cart_remove(request, product_id):
    logger.info(f"Removing product {product_id} from cart. Session ID: {request.session.session_key}")
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    response_data = {
        'success': True,
        'cart_count': int(cart.get_total_items()),
        'message': f'{product.name} removed from cart'
    }
    if is_ajax(request):
        return JsonResponse(response_data)
    messages.success(request, f'{product.name} removed from cart')
    return redirect('cart:cart_detail')

@require_POST
@safe_cart_operation
def cart_update(request, product_id):
    logger.info(f"Updating product {product_id}")
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
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
        cart.remove(product)
        message = f'{product.name} removed from cart'
    response_data = {
        'success': True,
        'cart_count': int(cart.get_total_items()),
        'message': message
    }
    if is_ajax(request):
        return JsonResponse(response_data)
    messages.success(request, message)
    return redirect('cart:cart_detail')

@safe_cart_operation
def cart_clear(request):
    logger.info(f"Clearing cart. Session ID: {request.session.session_key}")
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
    try:
        cart = Cart(request)
        logger.info(f"Displaying cart. Session ID: {request.session.session_key}")
        cart_items = []
        if hasattr(cart, 'get_cart_data_for_json'):
            cart_items = cart.get_cart_data_for_json()
        else:
            for item in cart:
                try:
                    product_id = item.get('product_id')
                    if not product_id:
                        logger.error(f"Invalid cart item: {item}")
                        continue
                    product = Product.objects.get(id=int(product_id))
                    if not product.available:
                        logger.warning(f"Product {product_id} is not available, removing from cart")
                        cart.remove(product)
                        continue
                    cart_items.append({
                        'product': product,
                        'name': item.get('name', ''),
                        'quantity': item.get('quantity', 0),
                        'price': float(item.get('price', 0)) if item.get('price') else 0,
                        'total_price': float(item.get('total_price', 0)) if item.get('total_price') else 0,
                        'image': item.get('image', ''),
                    })
                except Product.DoesNotExist:
                    logger.error(f"Product {item.get('product_id')} not found, removing from cart")
                    cart.remove(Product(id=item.get('product_id')))
                    continue
                except Exception as e:
                    logger.error(f"Error processing cart item {item}: {str(e)}")
                    continue
        total_price = float(cart.get_total_price() or 0)
        context = {
            'cart': cart_items,
            'cart_total_price': total_price,
        }
        if is_ajax(request):
            return JsonResponse(convert_decimals_to_float(context), cls=DecimalEncoder)
        return render(request, 'cart/detail.html', context)
    except Exception as e:
        logger.error(f"Critical error in cart_detail: {str(e)}")
        request.session.pop('cart', None)
        context = {
            'cart': [],
            'cart_total_price': 0.0,
        }
        if is_ajax(request):
            return JsonResponse(convert_decimals_to_float(context), cls=DecimalEncoder)
        messages.error(request, 'There was an error loading your cart. Your cart has been cleared.')
        return render(request, 'cart/detail.html', context)