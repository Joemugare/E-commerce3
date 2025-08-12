from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from reviews.models import Review


def product_list(request, category_slug=None):
    """Display a list of products, optionally filtered by category."""
    category = None
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
        'products': products,
    }
    return render(request, 'products/list.html', context)


def product_detail(request, id, slug):
    """Display product details with reviews and related products."""
    product = get_object_or_404(Product, id=id, slug=slug, available=True)

    reviews = Review.objects.filter(product=product, active=True)[:5]

    user_has_reviewed = False
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(product=product, user=request.user)
            user_has_reviewed = True
        except Review.DoesNotExist:
            pass

    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'reviews': reviews,
        'user_has_reviewed': user_has_reviewed,
        'user_review': user_review,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)


def product_search(request):
    """Search products by name or description."""
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            available=True
        ).distinct()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'products/search.html', {
        'query': query,
        'page_obj': page_obj,
    })


def category_list(request):
    """Display all categories."""
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})


def test_cart(request):
    """Test page for adding a product to cart."""
    product = Product.objects.first()
    if not product:
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=100,
            stock=10,
            available=True
        )
    return render(request, 'products/test.html', {'product': product})
