from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import ItemDetails, ItemImage, Item, OrderInfo, Order, OrderItem, CartItem, Address, \
    ItemCategory


class ItemImageInline(admin.TabularInline):  # Inline for Item Images
    model = ItemImage
    extra = 1
    fields = ('image',)


class ItemInline(admin.TabularInline):  # Inline for Items
    model = Item
    extra = 1
    fields = ('item_price','item_stock', 'article_id')

@admin.register(ItemDetails)
class ItemDetailsAdmin(admin.ModelAdmin):
    list_display = ('item_name',)
    inlines = [ItemImageInline, ItemInline]
    search_fields = ('item_name', 'item_description', 'items__article_id')
    ordering = ('item_name',)


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    search_fields = ('category_name',)
    ordering = ('category_name',)


class OrderInfoInline(admin.StackedInline):  # StackedInline for better readability
    model = OrderInfo
    extra = 0  # No extra blank forms


class OrderItemInline(admin.TabularInline):  # Inline for Order Items
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'order_date', 'order_total', 'order_active', 'order_status')
    list_filter = ('order_active', 'order_date', 'order_status',)
    search_fields = ('order_id', 'user__email', 'user__first_name', 'user__last_name')
    inlines = [OrderInfoInline, OrderItemInline]  # Added OrderInfoInline
    ordering = ('-order_date',)


class CartItemInline(admin.TabularInline):  # Inline for Cart Items
    model = CartItem
    extra = 1


# Inline for User Orders
class UserOrderInline(admin.TabularInline):
    model = Order
    extra = 0
    fields = ('order_id', 'order_date', 'order_total', 'order_status')
    readonly_fields = ('order_id', 'order_date', 'order_total', 'order_status')
    show_change_link = True  # Adds a link to the related order's admin page


class UserAddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('address', 'billing',)
    readonly_fields = ('address', 'billing',)


@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'company_name', 'company_identifier')
    ordering = ('email',)
    readonly_fields = ('email', 'first_name', 'last_name', 'company_name', 'company_identifier')
    inlines = [UserOrderInline, UserAddressInline]
    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'company_name', 'company_identifier')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
