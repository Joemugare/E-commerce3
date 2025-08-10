from django.shortcuts import render
from products.models import Product, Category

def home(request):
    """Home page view"""
    featured_products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    scrolling_products = Product.objects.filter(available=True)[:10]  # For ticker
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'scrolling_products': scrolling_products,
    }
    return render(request, 'core/home.html', context)

def search(request):
    """Search page view"""
    query = request.GET.get('q', '')
    featured_products = Product.objects.filter(name__icontains=query, available=True)[:8] if query else Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    scrolling_products = Product.objects.filter(available=True)[:10]  # For ticker
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'scrolling_products': scrolling_products,
        'query': query,
    }
    return render(request, 'core/home.html', context)

def about(request):
    """About page view"""
    scrolling_products = Product.objects.filter(available=True)[:10]  # For ticker
    context = {'scrolling_products': scrolling_products}
    return render(request, 'core/about.html', context)

def contact(request):
    """Contact page view"""
    scrolling_products = Product.objects.filter(available=True)[:10]  # For ticker
    context = {'scrolling_products': scrolling_products}
    return render(request, 'core/contact.html', context)