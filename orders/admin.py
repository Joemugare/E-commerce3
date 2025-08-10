from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'email',
                   'address', 'postal_code', 'city', 'paid', 'status', 'created', 'updated']
    list_filter = ['paid', 'status', 'created', 'updated']
    list_editable = ['paid', 'status']
    search_fields = ['first_name', 'last_name', 'email', 'address']
    inlines = [OrderItemInline]
    date_hierarchy = 'created'
    ordering = ['-created']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'price', 'quantity']
    list_filter = ['order__created']
    search_fields = ['order__id', 'product__name']