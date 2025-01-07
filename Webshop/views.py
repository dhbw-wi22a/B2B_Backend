from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from django.db import transaction
from .models import Order, OrderItem, Item, OrderInfo, ItemDetails, CustomUser
from .serializers import OrderSerializer, OrderItemSerializer, OrderInfoSerializer,  \
    ItemSerializer


def default_view(request):
    return JsonResponse({"message": "OK"})


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A ViewSet for listing and retrieving Items.
    """
    queryset = Item.objects.select_related('item_details').all()
    serializer_class = ItemSerializer


class OrderViewSet(viewsets.ViewSet):
    """
    A ViewSet for creating orders (POST only).
    """


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Handle the creation of an order.
        """
        # Pass the request data directly to the serializer
        serializer = OrderSerializer(data=request.data)

        # Let the serializer handle validation
        serializer.is_valid(raise_exception=True)

        # Save the validated data via the serializer (delegating to the manager)
        order = serializer.save()

        # Return the serialized response
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """
        Disable GET /orders/ for listing orders.
        """
        return Response({"error": "GET method is not allowed on orders."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Disable GET /orders/{id}/ for retrieving orders.
        """
        return Response({"error": "GET method is not allowed on orders."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        """
        Disable PUT/PATCH for orders.
        """
        return Response({"error": "PUT/PATCH methods are not allowed on orders."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        """
        Disable DELETE for orders.
        """
        return Response({"error": "DELETE method is not allowed on orders."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "The passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

