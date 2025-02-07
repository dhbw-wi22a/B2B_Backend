from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from utils.product_upload import process_product_upload
from .models import ItemDetails, ItemImage, Item, OrderInfo, Order, OrderItem, CartItem, Address, \
    ItemCategory, CompanyGroup, CompanyGroupMembership, GroupInvitation, ShoppingList, ShoppingListItem


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

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv), name='itemdetails_upload_csv'),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        """CSV-Upload für Produkte über das Admin-Panel."""
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")

            if not csv_file:
                messages.error(request, "Keine Datei hochgeladen!")
                return redirect("admin:itemdetails_upload_csv")

            try:
                process_product_upload(csv_file)  # CSV-Datei verarbeiten
                messages.success(request, "Produkte erfolgreich hochgeladen!")
                return redirect("admin:Webshop_itemdetails_changelist")

            except ValidationError as e:
                messages.error(request, f"Fehler beim Upload: {e}")
            except Exception as e:
                messages.error(request, f"Unerwarteter Fehler: {e}")

        return render(request, "admin/csv_upload.html", {"title": "CSV-Upload"})

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['upload_form'] = True
        return super().changelist_view(request, extra_context)

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


class CompanyGroupMembershipInline(admin.TabularInline):
    model = CompanyGroupMembership
    extra = 1
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ('joined_at',)

@admin.register(CompanyGroup)
class CompanyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner__email')
    inlines = [CompanyGroupMembershipInline]

@admin.register(CompanyGroupMembership)
class CompanyGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    search_fields = ('user__email', 'group__name')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:
            # New entries should only have the 'member' role
            form.base_fields['role'].choices = [
               choice for choice in CompanyGroupMembership._meta.get_field('role').choices if choice[0] == 'member'
            ]
        return form

class ShoppingListItemInline(admin.TabularInline):
    model = ShoppingListItem
    extra = 1
    fields = ('item', 'quantity')

@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'status', 'created_at')
    search_fields = ('title', 'group__name', 'created_by__email')
    inlines = [ShoppingListItemInline]
    list_display = ('title', 'created_by', 'created_at', 'status', 'number_of_items')

    def number_of_items(self, obj):
        return obj.shopping_list_items.count()

    number_of_items.short_description = 'Anzahl der Artikel'

@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'group', 'invited_by', 'status', 'created_at')
    search_fields = ('email', 'group__name', 'invited_by__email')