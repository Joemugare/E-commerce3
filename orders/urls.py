from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order creation and checkout
    path('checkout/', views.checkout, name='checkout'),  # Display checkout page with cart contents
    path('create/', views.order_create, name='order_create'),  # Create a new order from cart
    
    # Order management
    path('<int:order_id>/', views.order_detail, name='order_detail'),  # View specific order details
    path('<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),  # Cancel an order
    
    # Order listing
    path('', views.order_list, name='order_list'),  # List all orders for the user
]