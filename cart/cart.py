from django.conf import settings
from decimal import Decimal
from products.models import Product
import logging

logger = logging.getLogger(__name__)

class Cart:
    """
    A shopping cart stored in the session.
    """

    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        logger.debug(f"Initialized cart for session {self.session.session_key}: {self.cart}")

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        logger.debug(f"Adding product {product_id} with quantity {quantity}, override: {override_quantity}")

        if not product.available:
            raise ValueError(f"Product {product.name} is not available")

        if product_id not in self.cart:
            self.cart[product_id] = {
                'product_id': product_id,
                'name': product.name,
                'price': str(product.price),  # Store as string for JSON serialization
                'quantity': 0,
                'image': product.image.url if product.image else ''
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        if self.cart[product_id]['quantity'] > product.stock:
            raise ValueError(f"Cannot add {quantity} of {product.name}. Only {product.stock} in stock.")

        if self.cart[product_id]['quantity'] <= 0:
            self.remove(product_id)

        self.save()

    def save(self):
        """
        Save the cart to the session, ensuring JSON-serializable data.
        """
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True
        logger.debug(f"Saved cart for session {self.session.session_key}: {self.cart}")

    def remove(self, product_id):
        """
        Remove a product from the cart.
        """
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        """
        Remove the cart from the session.
        """
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True
        logger.debug(f"Cleared cart for session {self.session.session_key}")

    def __iter__(self):
        """
        Iterate over the items in the cart, including Product objects.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids).select_related()
        product_map = {str(product.id): product for product in products}
        for product_id, item in self.cart.items():
            product = product_map.get(product_id)
            if not product:
                logger.warning(f"Product {product_id} not found, removing from cart")
                self.remove(product_id)
                continue
            yield {
                'product': product,
                'product_id': product_id,
                'name': item['name'],
                'quantity': item['quantity'],
                'price': Decimal(item['price']),  # Convert back to Decimal
                'total_price': Decimal(item['price']) * item['quantity'],
                'image': item['image']
            }

    def __len__(self):
        """
        Return the total quantity of all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values() if item.get('quantity', 0) > 0)

    def get_total_price(self):
        """
        Return the total cost of all items in the cart.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values() if item.get('quantity', 0) > 0)

    def get_total_items(self):
        """
        Return the total quantity of all items in the cart.
        """
        return self.__len__()

    def get_cart_data_for_json(self):
        """
        Return cart data as a list of dictionaries for JSON serialization.
        """
        cart_items = []
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids).select_related()
        product_map = {str(product.id): product for product in products}
        for product_id, item in self.cart.items():
            product = product_map.get(product_id)
            if not product:
                logger.error(f"Product {product_id} not found, removing from cart")
                self.remove(product_id)
                continue
            cart_items.append({
                'product': product,
                'product_id': product_id,
                'name': item['name'],
                'quantity': item['quantity'],
                'price': float(item['price']),  # Convert to float for JSON
                'total_price': float(Decimal(item['price']) * item['quantity']),
                'image': item['image']
            })
        return cart_items