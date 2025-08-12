from django.urls import path
from . import views
from products.views import test_cart

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('search/', views.product_search, name='search'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('test/', test_cart, name='test_cart'),  # only one path, let APPEND_SLASH handle redirects
]
