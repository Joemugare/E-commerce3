from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created', 'updated']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['created', 'updated']
    date_hierarchy = 'created'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'price', 'available', 'stock', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'available', 'stock']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    date_hierarchy = 'created'
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Price & Stock', {
            'fields': ('price', 'stock', 'available')
        }),
        ('Media', {
            'fields': ('image',)
        }),
    )