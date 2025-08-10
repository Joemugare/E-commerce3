from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import OrderCreateForm


@login_required
def order_create(request):
    """
    Create a new order from the current cart.
    """
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # Create order items from cart items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            # Clear the cart after order is placed
            cart.clear()

            messages.success(request, f'Order {order.id} created successfully!')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderCreateForm()
    
    return render(request, 'orders/order/create.html', {
        'cart': cart,
        'form': form
    })


@login_required
def order_detail(request, order_id):
    """
    Display the details of a specific order.
    """
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    except Http404:
        messages.error(request, 'Order not found.')
        return redirect('orders:order_list')
    
    return render(request, 'orders/order/detail.html', {'order': order})


@login_required
def order_list(request):
    """
    Show all orders for the logged-in user.
    """
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order/list.html', {'orders': orders})


@login_required
def order_cancel(request, order_id):
    """
    Cancel an order if it's in 'pending' or 'processing' status.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['pending', 'processing']:
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order {order.id} has been cancelled.')
    else:
        messages.error(request, f'Order {order.id} cannot be cancelled at this stage.')
    
    return redirect('orders:order_detail', order_id=order.id)


@login_required
def checkout(request):
    """
    Display the checkout page with current cart contents.
    """
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    # Render a simple checkout page (can be extended)
    return render(request, 'orders/checkout.html', {'cart': cart})
