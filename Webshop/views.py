from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, serializers, generics
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from .models import Order, OrderItem, Item, OrderInfo, ItemDetails, CustomUser as User, ShoppingCart, Address
from .serializers import OrderSerializer, OrderItemSerializer, OrderInfoSerializer, \
    ItemSerializer, UserRegistrationSerializer, UserSerializer, ShoppingCartSerializer, UserShortSerializer, \
    CartItemSerializer, AddressSerializer


def default_view(request):
    return JsonResponse({"message": "OK"})

# 1. User Registration View
class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer


# 2. User Management View (Detail & Update)
class BaseUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']


    def get_queryset(self):
        return self.queryset.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # Ensure email remains unchanged
        serializer.save(email=self.request.user.email)

    def perform_destroy(self, instance):
        # Deactivate user instead of deleting
        instance.set_inactive()

    @action(detail=False, methods=['patch'], url_path='update')
    def update_user(self, request, pk=None):
        """
        Update the user's profile.
        """
        serializer = UserSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)



class UserShortView(BaseUserViewSet):
    serializer_class = UserShortSerializer

    def get_view_name(self):
        return "My Profile"


class UserView(BaseUserViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related(
            'addresses',
            'shopping_cart__cartitem_set__item'
        )
        return queryset

    def get_view_name(self):
        return "My Profile Detail"



# 3. Order Management View
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('orderitem_set__item')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head']

    filterset_fields = ['order_status', 'order_date', 'order_total']
    ordering_fields = ['order_date', 'order_total', 'order_status']
    ordering = ['-order_date']


    def get_queryset(self):
        # Return only orders belonging to the logged-in user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Attach the current user to the order during creation
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        # Prevent updating orders
        return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        # Prevent deleting orders
        return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# 4. Shopping Cart View
class ShoppingCartViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShoppingCart.objects.prefetch_related('cartitem_set__item')
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only the shopping cart of the logged-in user
        return self.queryset.filter(user=self.request.user)

    def get_list(self, request, *args, **kwargs):
        # Return only the shopping cart of the logged-in user
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.shopping_cart


    @action(detail=False, methods=['post'], url_path='set')
    def set_item(self, request, pk=None):
        """
        Add item to the shopping cart.
        """
        serializer = CartItemSerializer(data=request.data)

        if serializer.is_valid():
            cart = self.get_object()
            item = serializer.validated_data['item']
            quantity = serializer.validated_data['quantity']
            cart.set_item(item, quantity)
            return Response({'status': 'Success'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'], url_path='clear')
    def clear_cart(self, request, pk=None):
        """
        Clear all items from the shopping cart.
        """
        cart = self.get_object()
        cart.clear()
        return Response({'status': 'Success'}, status=status.HTTP_204_NO_CONTENT)

# 5. Address View
class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only addresses belonging to the logged-in user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Attach the current user to the address during creation
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure the address belongs to the current user
        if serializer.instance.user != self.request.user:
            raise MethodNotAllowed(method='PUT')
        serializer.save()

    def perform_destroy(self, instance):
        # Ensure the address belongs to the current user
        if instance.user != self.request.user:
            raise MethodNotAllowed(method='DELETE')
        instance.delete()

    @action(detail=False, methods=['get'], url_path='billing')
    def get_billing_address(self, request, pk=None):
        try:
           # Attempt to fetch the billing address for the user
           address = self.queryset.get(billing=True)
           serializer = AddressSerializer(address)
           return Response(serializer.data, status=status.HTTP_200_OK)
        except Address.DoesNotExist:
           # Handle the case where no billing address exists
           return Response(
               {"detail": "Billing address not found."},
               status=status.HTTP_404_NOT_FOUND
           )


# 6. Item View (Product Listings)
class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.prefetch_related('item_details__images')
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'item_price': ['exact', 'lte', 'gte'],  # Dynamic price filtering
        'item_details__categories__category_name': ['exact', 'icontains'],  # Dynamic category filtering
        'item_details__item_name': ['exact', 'icontains'],  # Dynamic name filtering
        'item_details__item_description': ['exact', 'icontains']  # Dynamic description filtering
    }
    ordering_fields = ['item_price', 'item_details__item_name']  # Specify sortable fields
    ordering = ['item_price']  # Default ordering
