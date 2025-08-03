from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from carts.models import Cart, CartItem,Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    fields = ['product', 'quantity']


class CartAdmin(GuardedModelAdmin):
    list_display = ['buyer', 'get_item_count']
    search_fields = ['buyer__username', 'buyer__email']
    inlines = [CartItemInline]

    def get_item_count(self, obj):
        return obj.cartitem_set.count()
    get_item_count.short_description = 'Items'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'price_at_time']


class OrderAdmin(GuardedModelAdmin):
    list_display = ['id', 'buyer', 'total_amount', 'created_at', 'get_item_count']
    list_filter = ['created_at', 'buyer']
    search_fields = ['buyer__username', 'buyer__email']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    def get_item_count(self, obj):
        return obj.items.count() if hasattr(obj, 'items') else OrderItem.objects.filter(order=obj).count()
    get_item_count.short_description = 'Items'


admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)