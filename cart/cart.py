from django.conf import settings
from decimal import Decimal
from products.models import Product
import logging

logger = logging.getLogger(__name__)

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        logger.debug(f"Initialized cart for session {self.session.session_key}: {self.cart}")

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        logger.debug(f"Adding product {product_id} with quantity {quantity}, override: {override_quantity}")
        if not product.available:
            raise ValueError(f"Product {product.name} is not available")
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'name': product.name,
                'image': product.image.url if product.image else ''
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        if self.cart[product_id]['quantity'] > product.stock:
            raise ValueError(f"Cannot add {quantity} of {product.name}. Only {product.stock} in stock.")
        self.save()

    def save(self):
        self.session.modified = True
        logger.debug(f"Saved cart for session {self.session.session_key}: {self.cart}")

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def __iter__(self):
        for product_id, item in self.cart.items():
            yield {
                'product_id': product_id,
                'name': item['name'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': Decimal(item['price']) * item['quantity'],
                'image': item['image']
            }

    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_cart_data_for_json(self):
        cart_items = []
        for product_id, item in self.cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                cart_items.append({
                    'product': product,
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'total_price': float(Decimal(item['price']) * item['quantity']),
                    'image': item['image']
                })
            except Product.DoesNotExist:
                logger.error(f"Product {product_id} not found, skipping")
                self.remove(Product(id=product_id))
                continue
        return cart_items