from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from products.models import Category, Product


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


class ProductAdmin(GuardedModelAdmin):
    list_display = ['name', 'farmer', 'category', 'price', 'quantity_available', 'harvest_date', 'expiry_date']
    list_filter = ['category', 'farmer']
    search_fields = ['name', 'description', 'farmer__username']
    date_hierarchy = 'harvest_date'
    fields = ['name', 'description', 'price', 'category', 'quantity_available', 'harvest_date', 'expiry_date', 'farmer']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)