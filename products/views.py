from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from reviews.models import Review


def product_list(request, category_slug=None):
    """Display list of products, optionally filtered by category."""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    # Filter by category from URL slug
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'name':
        products = products.order_by('name')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created')

    # Price filter
    price = request.GET.get('price')
    if price == 'low':
        products = products.filter(price__lt=5000)
    elif price == 'medium':
        products = products.filter(price__gte=5000, price__lte=20000)
    elif price == 'high':
        products = products.filter(price__gt=20000)

    # Pagination: 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/product_list.html', {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,  # ✅ matches your template
    })


def product_detail(request, id, slug):
    """Display product details."""
    product = get_object_or_404(Product, id=id, slug=slug, available=True)

    # Reviews
    reviews = Review.objects.filter(product=product, active=True)[:5]

    # Check if the current user has reviewed this product
    user_has_reviewed = False
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(product=product, user=request.user)
            user_has_reviewed = True
        except Review.DoesNotExist:
            pass

    # Related products (same category, excluding current)
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]

    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'user_has_reviewed': user_has_reviewed,
        'user_review': user_review,
        'related_products': related_products,
    })


def product_search(request):
    """Search products by name or description."""
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            available=True
        ).distinct()

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/search.html', {
        'query': query,
        'page_obj': page_obj,  # ✅ match template
    })


def category_list(request):
    """Display all categories."""
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {
        'categories': categories
    })
