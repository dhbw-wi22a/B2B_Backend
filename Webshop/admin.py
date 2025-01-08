from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import ItemDetails, ItemImage, Item, OrderInfo, Order, OrderItem, ShoppingCart, CartItem


class ItemImageInline(admin.TabularInline):  # Inline for Item Images
    model = ItemImage
    extra = 1
    fields = ('image',)


class ItemInline(admin.TabularInline):  # Inline for Items
    model = Item
    extra = 1
    fields = ('item_price',)


@admin.register(ItemDetails)
class ItemDetailsAdmin(admin.ModelAdmin):
    list_display = ('item_name','article_id','item_stock')
    inlines = [ItemImageInline, ItemInline]
    search_fields = ('item_name','article_id')
    ordering = ('item_name',)


class OrderInfoInline(admin.StackedInline):  # StackedInline for better readability
    model = OrderInfo
    extra = 0  # No extra blank forms


class OrderItemInline(admin.TabularInline):  # Inline for Order Items
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'order_date', 'order_total', 'order_active')
    list_filter = ('order_active', 'order_date')
    inlines = [OrderInfoInline, OrderItemInline]  # Added OrderInfoInline
    ordering = ('-order_date',)


class CartItemInline(admin.TabularInline):  # Inline for Cart Items
    model = CartItem
    extra = 1


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    ordering = ('-created_at',)

@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)
    readonly_fields = ('email',)
    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )

