from rest_framework import serializers

from .models import Item, Order, OrderInfo, OrderItem, ItemImage, ItemDetails, CustomUser, Address, ShoppingCart, \
    CartItem


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
        fields = ['item_details_id', 'item_name', 'item_description', 'images']


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Item model, including nested ItemDetails.
    """
    item_details = ItemDetailSerializer(read_only=True)

    class Meta:
        model = Item
        fields = ['item_id', 'item_price', 'item_details']


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

    fields = [
        'order_id',
        'order_active',
        'order_status',
        'order_date',
        'order_total',
        'order_info',
        'items',
        'items_read',
    ]
    class Meta:
        model = Order
        extra_kwargs = {
            'items': {'write_only': True},
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
                  'company_id',
                  'company_name',
                  'phone',
                  'first_name',
                  'last_name',
                  'full_name',
                  ]
        read_only_fields = ['email', 'full_name']



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
        fields = ['cart_id', 'items', 'updated_at']

    def get_items(self, obj):
        # Use prefetch_related to optimize database hits
        cart_items = obj.cartitem_set.all().select_related('item')
        return CartItemSerializer(cart_items, many=True).data

class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shopping_cart = ShoppingCartSerializer(read_only=True)
    class Meta:
        model = CustomUser
        fields = ['email',
                  'company_id',
                  'company_name',
                  'phone',
                  'first_name',
                  'last_name',
                  'full_name',
                  'addresses',
                  'billing_address',
                  'shopping_cart',
                  ]
        read_only_fields = ['email', 'full_name', 'shopping_cart',]

class UserOrdersSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'orders']
        read_only_fields = ['email', 'orders']

