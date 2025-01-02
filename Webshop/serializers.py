from rest_framework import serializers
from .models import Item, Order, OrderInfo, OrderItem, ItemImage, ItemDetails


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
        fields = ['item_details_id', 'item_name', 'item_description','article_id','item_stock','images']


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
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())

    class Meta:
        model = OrderItem
        fields = ['item', 'quantity']


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

    class Meta:
        model = Order
        fields = ['order_id', 'order_date', 'order_total', 'order_active', 'order_info', 'items']

    def validate(self, data):
        """
        Custom validation to ensure nested fields are valid.
        """
        if not data.get('order_info'):
            raise serializers.ValidationError({"order_info": "This field is required."})

        if not data.get('items'):
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

    def to_representation(self, instance):
        """
        Customize the representation to include nested order info and items.
        """
        representation = super().to_representation(instance)
        representation['order_info'] = OrderInfoSerializer(instance.order_info).data
        representation['items'] = OrderItemSerializer(instance.orderitem_set.all(), many=True).data
        return representation
