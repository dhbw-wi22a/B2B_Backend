from rest_framework import serializers

from .models import Item, Order, OrderInfo, OrderItem, ItemImage, ItemDetails, CustomUser, Address, ShoppingCart, \
    CartItem, CompanyGroup, CompanyGroupMembership, GroupInvitation, ShoppingList, ShoppingListItem


class ItemImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ItemImage model.
    """

    class Meta:
        model = ItemImage
        fields = ['image_id', 'image']


class ItemDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for ItemDetails model, including associated images.
    """
    images = ItemImageSerializer(many=True, read_only=True)

    class Meta:
        model = ItemDetails
        fields = ['item_details_id', 'item_name', 'item_description', 'images', 'categories']


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Item model, including nested ItemDetails.
    """
    item_details = ItemDetailSerializer(read_only=True)

    class Meta:
        model = Item
        fields = ['item_id', 'item_price', 'item_details', 'item_stock', 'article_id']


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    """
    item = ItemSerializer(read_only=True)  # Show item details for read
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), write_only=True, source='item')

    class Meta:
        model = OrderItem
        fields = ['item', 'item_id', 'quantity']


class OrderInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderInfo model.
    """

    class Meta:
        model = OrderInfo
        fields = ['buyer_name', 'buyer_email', 'buyer_phone', 'buyer_address']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model with nested order info and items.
    """
    order_info = OrderInfoSerializer()
    items = OrderItemSerializer(many=True, write_only=True)
    items_read = serializers.SerializerMethodField()  # Read-only field for items

    class Meta:
        model = Order
        fields = [
            'order_id',
            'order_status',
            'order_date',
            'order_total',
            'order_info',
            'items',
            'items_read',
        ]
        extra_kwargs = {
            'items': {'write_only': True},
            'order_total': {'read_only': True},
            'order_date': {'read_only': True},
            'order_status': {'read_only': True},
            'order_id': {'read_only': True},
        }

    def validate(self, data):
        """
        Custom validation to ensure nested fields are valid.
        """
        if 'order_info' not in data:
            raise serializers.ValidationError({"order_info": "This field is required."})

        if 'items' not in data or not data['items']:
            raise serializers.ValidationError({"items": "At least one item is required to create an order."})

        return data

    def create(self, validated_data):
        """
        Use the custom manager to handle order creation.
        """
        order_info_data = validated_data.pop('order_info')
        items_data = validated_data.pop('items')

        # Delegate creation to the manager
        order = Order.objects.create_with_info_and_items(
            order_info_data=order_info_data,
            items_data=items_data,
            **validated_data
        )
        return order

    def get_items_read(self, obj):
        """
        Get items for read operations, optimizing with select_related.
        """
        items = obj.orderitem_set.select_related('item')
        return OrderItemSerializer(items, many=True).data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password_confirm']

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "The passwords do not match."})
        return data

    def create(self, validated_data):
        # Remove the password_confirm field as it is not used in user creation
        validated_data.pop('password_confirm')
        # Use the model manager to create a user
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email',
                  'company_identifier',
                  'company_name',
                  'phone',
                  'first_name',
                  'last_name',
                  'full_name',
                  ]
        extra_kwargs = {
            'full_name': {'read_only': True},
            'email': {'read_only': True},
        }


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['address_id', 'address', 'billing']


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['item', 'quantity']


class ShoppingCartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingCart
        fields = ['items', 'updated_at']

    def get_items(self, obj):
        cart_items = obj.cartitem_set.all()
        return CartItemSerializer(cart_items, many=True).data


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shopping_cart = ShoppingCartSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'company_identifier',
            'company_name',
            'phone',
            'first_name',
            'last_name',
            'full_name',
            'addresses',
            'billing_address',
            'shopping_cart',
        ]
        extra_kwargs = {
            'full_name': {'read_only': True},
            'email': {'read_only': True},
        }


class UserOrdersSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'orders']
        extra_kwargs = {
            'email': {'read_only': True},
            'orders': {'read_only': True},
        }



class CompanyGroupMembershipSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    class Meta:
        model = CompanyGroupMembership
        fields = ['user', 'group', 'role', 'joined_at']
        read_only_fields = ['joined_at']
        extra_kwargs = {
            'group': {'read_only': True},
        }

class CompanyGroupSerializer(serializers.ModelSerializer):
    members = CompanyGroupMembershipSerializer(many=True, read_only=True)
    class Meta:
        model = CompanyGroup
        fields = ['id', 'name', 'owner', 'members']
        read_only_fields = ['id', 'owner']

        extra_kwargs = {
            'owner': {'read_only': True},
        }

class GroupInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvitation
        fields = ['id', 'email', 'group', 'invited_by', 'status', 'created_at']
        read_only_fields = ['id', 'invited_by', 'created_at']


class ShoppingListItemsSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), write_only=True, source='item')

    class Meta:
        model = ShoppingListItem
        fields = ['id', 'shopping_list', 'item', 'item_id', 'quantity']
        read_only_fields = ['id', 'shopping_list']
        extra_kwargs = {
            'shopping_list': {'required': True},
            'item': {'required': True},
            'quantity': {'required': True, 'min_value': 1},
        }

class ShoppingListSerializer(serializers.ModelSerializer):
    items = ShoppingListItemsSerializer(source='shopping_list_items', many=True, read_only=True)
    items_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ShoppingList
        fields = ['id', 'title', 'group', 'created_at', 'created_by', 'items', 'items_data', 'status', 'is_personal']
        read_only_fields = ['id', 'created_at', 'created_by']

    def create(self, validated_data):
        items_data = validated_data.pop('items_data', [])
        shopping_list = super().create(validated_data)

        for item_data in items_data:
            ShoppingListItem.objects.create(shopping_list=shopping_list, **item_data)

        return shopping_list

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items_data', [])
        shopping_list = super().update(instance, validated_data)

        shopping_list.shopping_list_items.all().delete()
        for item_data in items_data:
            ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                item_id=item_data['item_id'],
                quantity=item_data.get('quantity', 1)
            )
        return shopping_list