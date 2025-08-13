import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.core.exceptions import ValidationError
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm

logger = logging.getLogger(__name__)


@login_required
def order_create(request):
    """
    Create a new order from the current cart.
    Validates cart items, creates order items, updates stock, and clears the cart.
    """
    cart = Cart(request)

    if not cart:
        logger.info(f"User {request.user.id} attempted to create order with empty cart")
        messages.warning(request, "Your cart is empty. Please add items before placing an order.")
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the order
                    order = form.save(commit=False)
                    order.user = request.user
                    order.save()

                    # Validate cart and prepare order items
                    order_items = []
                    stock_errors = []
                    
                    for item in cart:
                        # Validate cart item structure
                        if not _is_valid_cart_item(item):
                            logger.warning(f"Invalid cart item structure for user {request.user.id}: {item}")
                            continue
                            
                        product = item["product"]
                        quantity = item["quantity"]
                        
                        # Check stock availability
                        if product.stock < quantity:
                            stock_errors.append(f"{product.name} (requested: {quantity}, available: {product.stock})")
                            continue
                            
                        # Create order item
                        order_items.append(OrderItem(
                            order=order,
                            product=product,
                            price=item["price"],
                            quantity=quantity
                        ))

                    # Handle stock errors
                    if stock_errors:
                        error_msg = "Insufficient stock for: " + ", ".join(stock_errors)
                        logger.warning(f"Stock validation failed for user {request.user.id}: {error_msg}")
                        messages.error(request, f"{error_msg}. Please adjust your cart.")
                        return redirect("cart:cart_detail")

                    # Handle empty valid items
                    if not order_items:
                        logger.error(f"No valid items for order creation by user {request.user.id}")
                        messages.error(request, "No valid items in your cart. Please add products and try again.")
                        return redirect("cart:cart_detail")

                    # Bulk create order items and update stock
                    OrderItem.objects.bulk_create(order_items)
                    
                    # Update product stock
                    for item in cart:
                        if _is_valid_cart_item(item) and item["product"].stock >= item["quantity"]:
                            product = item["product"]
                            product.stock -= item["quantity"]
                            product.save(update_fields=['stock'])

                    # Clear cart and redirect
                    cart.clear()
                    logger.info(f"Order #{order.id} created successfully for user {request.user.id} with {len(order_items)} items")
                    messages.success(request, f"Order #{order.id} created successfully!")
                    return redirect("orders:order_detail", order_id=order.id)
                    
            except ValidationError as e:
                logger.error(f"Validation error during order creation for user {request.user.id}: {str(e)}")
                messages.error(request, "Please check your order details and try again.")
            except Exception as e:
                logger.error(f"Unexpected error during order creation for user {request.user.id}: {str(e)}")
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            logger.warning(f"Form validation failed for user {request.user.id}: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = OrderCreateForm()

    return render(request, "orders/create.html", {
        "cart": cart, 
        "form": form,
        "total_cost": cart.get_total_price()
    })


@login_required
def order_detail(request, order_id):
    """
    Display details of a specific order for the logged-in user.
    """
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        logger.debug(f"User {request.user.id} accessing order #{order_id}")
        
        context = {
            "order": order,
            "can_cancel": order.status in ["pending", "processing"]
        }
        
        return render(request, "orders/details.html", context)
        
    except Http404:
        logger.warning(f"User {request.user.id} attempted to access non-existent or unauthorized order #{order_id}")
        messages.error(request, "Order not found or you don't have permission to view it.")
        return redirect("orders:order_list")
    except Exception as e:
        logger.error(f"Error accessing order #{order_id} for user {request.user.id}: {str(e)}")
        messages.error(request, "An error occurred while loading the order details.")
        return redirect("orders:order_list")


@login_required
def order_list(request):
    """
    List all orders for the logged-in user with pagination and filtering.
    """
    try:
        orders = Order.objects.filter(user=request.user).select_related('user').prefetch_related('items__product').order_by("-created")
        
        # Optional: Add status filtering
        status_filter = request.GET.get('status')
        if status_filter and status_filter in [choice[0] for choice in Order.STATUS_CHOICES]:
            orders = orders.filter(status=status_filter)
        
        logger.debug(f"User {request.user.id} accessed order list: {orders.count()} orders")
        
        context = {
            "orders": orders,
            "status_choices": Order.STATUS_CHOICES,
            "current_status": status_filter
        }
        
        return render(request, "orders/list.html", context)
        
    except Exception as e:
        logger.error(f"Error loading order list for user {request.user.id}: {str(e)}")
        messages.error(request, "An error occurred while loading your orders.")
        return render(request, "orders/list.html", {"orders": Order.objects.none()})


@login_required
def order_cancel(request, order_id):
    """
    Cancel an order if it is in cancellable status.
    Restores product stock when order is cancelled.
    """
    if request.method != "POST":
        logger.warning(f"Invalid method for order cancellation by user {request.user.id}: {request.method}")
        messages.error(request, "Invalid request method.")
        return redirect("orders:order_list")
    
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        if order.status not in ["pending", "processing"]:
            logger.warning(f"User {request.user.id} attempted to cancel order #{order.id} with status '{order.status}'")
            messages.error(request, f"Order #{order.id} cannot be cancelled at this stage (Status: {order.get_status_display()}).")
            return redirect("orders:order_detail", order_id=order.id)
        
        with transaction.atomic():
            # Restore stock for cancelled order
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save(update_fields=['stock'])
            
            # Update order status
            order.status = "cancelled"
            order.save(update_fields=['status'])
            
        logger.info(f"Order #{order.id} cancelled by user {request.user.id}, stock restored")
        messages.success(request, f"Order #{order.id} has been cancelled successfully.")
        
    except Http404:
        logger.warning(f"User {request.user.id} attempted to cancel non-existent or unauthorized order #{order_id}")
        messages.error(request, "Order not found or you don't have permission to cancel it.")
        return redirect("orders:order_list")
    except Exception as e:
        logger.error(f"Error cancelling order #{order_id} for user {request.user.id}: {str(e)}")
        messages.error(request, "An error occurred while cancelling the order.")
    
    return redirect("orders:order_detail", order_id=order.id)


@login_required
def checkout(request):
    """
    Display the checkout page with current cart contents and shipping options.
    """
    cart = Cart(request)
    
    if not cart:
        logger.info(f"User {request.user.id} accessed checkout with empty cart")
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect("cart:cart_detail")
    
    # Validate cart items before checkout
    invalid_items = []
    for item in cart:
        if not _is_valid_cart_item(item):
            invalid_items.append(item)
        elif item["product"].stock < item["quantity"]:
            invalid_items.append(item)
    
    if invalid_items:
        logger.warning(f"User {request.user.id} has invalid items in cart during checkout")
        messages.warning(request, "Some items in your cart are no longer available. Please review your cart.")
        return redirect("cart:cart_detail")
    
    logger.debug(f"User {request.user.id} accessed checkout: {cart.get_total_items()} items, total: {cart.get_total_price()}")
    
    context = {
        "cart": cart,
        "total_items": cart.get_total_items(),
        "total_cost": cart.get_total_price(),
        "form": OrderCreateForm()
    }
    
    return render(request, "orders/checkout.html", context)


def _is_valid_cart_item(item):
    """
    Helper function to validate cart item structure.
    """
    required_keys = ("product", "price", "quantity")
    if not all(k in item for k in required_keys):
        return False
    if item["quantity"] <= 0:
        return False
    if item["price"] <= 0:
        return False
    return True