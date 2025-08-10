from django.contrib import admin
from .models import Review, ReviewHelpful


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'user', 'rating', 'title', 'active', 'created']
    list_filter = ['active', 'rating', 'created', 'product']
    list_editable = ['active']
    search_fields = ['title', 'comment', 'user__username', 'product__name']
    readonly_fields = ['created', 'updated']
    date_hierarchy = 'created'
    ordering = ['-created']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'user', 'rating', 'title', 'comment', 'active')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created']
    list_filter = ['created']
    search_fields = ['review__title', 'user__username']
    date_hierarchy = 'created'