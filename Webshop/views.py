from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    INTERNAL_RESET_SESSION_TOKEN
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.message import utf8_charset
from django.db import models
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated



from utils.mail_service import send_group_invitation_mail, send_password_reset_mail
from .models import Order, Item, CustomUser as User, ShoppingCart, Address, VerificationToken, CompanyGroup, CompanyGroupMembership, CompanyGroupRole, GroupInvitation, ShoppingList, ShoppingListItem, GroupInvitationStatus
from .serializers import OrderSerializer, ItemSerializer, UserRegistrationSerializer, UserSerializer, \
    ShoppingCartSerializer, UserShortSerializer, \
    CartItemSerializer, AddressSerializer, CompanyGroupMembershipSerializer, CompanyGroupSerializer, \
    GroupInvitationSerializer, ShoppingListSerializer, ShoppingListItemsSerializer


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

    @action(detail=False, methods=['delete'], url_path='delete')
    def delete_user(self, request, pk=None):
        """
        Deactivate the user's profile.
        """
        user = self.get_object()
        self.perform_destroy(user)
        return Response({'status': 'User set successfully. to inactive.'},status=status.HTTP_204_NO_CONTENT)

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
    http_method_names = ['get', 'post', 'head']

    filterset_fields = ['order_status', 'order_date', 'order_total']
    ordering_fields = ['order_date', 'order_total', 'order_status']
    ordering = ['-order_date']

    def get_queryset(self):
        # Return only orders belonging to the logged-in user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Attach the current user to the order during creation
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def update(self, request, *args, **kwargs):
        # Prevent updating orders
        return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        # Prevent deleting orders
        return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_permissions(self):
        # Allow anonymous users to create orders; restrict others to authenticated users
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


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


# 7. Email Verification
class EmailVerificationView(ViewSet):
    @action(detail=False, methods=['get'], url_path='verify/(?P<token>[^/.]+)')
    def verify_email(self, request, token):
        try:
            verification_token = VerificationToken.objects.get(token=token)
        except VerificationToken.DoesNotExist:
            return JsonResponse({"message": "Dieser Verifizierungslink wurde bereits verwendet oder ist ungültig."},status=400)

        user = verification_token.user
        user.verified = True
        user.save(update_fields=['verified'])
        verification_token.delete()

        return JsonResponse({"message": "E-Mail erfolgreich bestätigt!"},status=200)


# 8. CompanyGroups View
class CompanyGroupViewSet(viewsets.ModelViewSet):
    queryset = CompanyGroup.objects.all()
    serializer_class = CompanyGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only groups the user is a member of
        return self.queryset.filter(companygroupmembership__user=self.request.user).distinct()

    def perform_create(self, serializer):
        # Attach the current user to the group during creation
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        # Ensure the group creator is the current user
        if serializer.instance.creator != self.request.user:
            raise MethodNotAllowed(method='PUT')
        serializer.save()

    def perform_destroy(self, instance):
        # Ensure the group creator is the current user
        if instance.creator != self.request.user:
            raise MethodNotAllowed(method='DELETE')
        instance.delete()

    @action(detail=True, methods=['post'], url_path='invite')
    def invite_member(self, request, pk=None):
        """
        Handle inviting a user to a group. Supports both registered and unregistered users.
        """
        group = self.get_object()
        email = request.data.get('email')

        if not email:
            raise ValidationError({"email": "Email is required."})

        # Prüfen, ob der Benutzer existiert
        user = User.objects.filter(email=email).first()
        if user:
            # Benutzer existiert bereits -> Einladung erstellen
            GroupInvitation.objects.create(
                email=email,
                group=group,
                invited_by=request.user
            )
            return Response(
                {'status': 'Invitation sent to the registered user.'},
                status=status.HTTP_200_OK
            )
        else:
            # Benutzer existiert nicht -> Einladung erstellen
            invitation = GroupInvitation.objects.create(
                email=email,
                group=group,
                invited_by=request.user
            )
            return Response(
                {'status': 'Invitation sent to unregistered user for registration.'},
                status=status.HTTP_201_CREATED
            )


# 9. GroupInvitations View
class GroupInvitationViewSet(viewsets.ModelViewSet):
    queryset = GroupInvitation.objects.all()
    serializer_class = GroupInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only invitations related to the logged-in user
        return self.queryset.filter(
            models.Q(invited_by=self.request.user) | models.Q(email=self.request.user.email)
        )

    @action(detail=False, methods=['get','post'], url_path='<uuid:token>/accept')
    def accept_invitation(self, request, token=None):
        """
        Allow a user to accept a group invitation without requiring authentication.
        """
        try:
            invitation = GroupInvitation.objects.get(
                group_invite_token=token,
                status=GroupInvitationStatus.PENDING
            )
        except GroupInvitation.DoesNotExist:
            return Response({"error": "Invalid or expired invitation."}, status=status.HTTP_400_BAD_REQUEST)

        # Handle user creation or retrieval
        user = User.objects.filter(email=invitation.email).first()
        if not user:
            return Response({"error": "User does not exist. Please register first."}, status=status.HTTP_400_BAD_REQUEST)

        # Accept the invitation
        invitation.status = GroupInvitationStatus.ACCEPTED
        invitation.save()

        # Add the user to the group
        CompanyGroupMembership.objects.create(user=user, group=invitation.group, role='member')

        return Response({"message": f"Invitation accepted for group {invitation.group.name}."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get','post'], url_path='<uuid:token>/decline')
    def decline_invitation(self, request, token=None):
        """
        Allow a user to decline a group invitation without requiring authentication.
        """
        try:
            invitation = GroupInvitation.objects.get(
                group_invite_token=token,
                status=GroupInvitationStatus.PENDING
            )
        except GroupInvitation.DoesNotExist:
            return Response({"error": "Invalid or expired invitation."}, status=status.HTTP_400_BAD_REQUEST)

        # Decline the invitation
        invitation.status = GroupInvitationStatus.DECLINED
        invitation.save()

        return Response({"message": f"Invitation declined for group {invitation.group.name}."}, status=status.HTTP_200_OK)

# 10. CompanyGroupMemberships View
class CompanyGroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = CompanyGroupMembership.objects.all()
    serializer_class = CompanyGroupMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CompanyGroupMembership.objects.filter(Q(user=user) | Q(group__owner=user)).distinct()

    def perform_add(self, serializer):
        # Only allow the owner of the group to add members
        group = serializer.validated_data['group']
        if group.owner != self.request.user:
            raise MethodNotAllowed('POST', 'Only the group owner can add members.')
        serializer.save()

    def perform_delete(self, instance):
        # Only allow the owner of the group to remove members
        if instance.group.owner != self.request.user:
            raise MethodNotAllowed('DELETE', 'Only the group owner can remove members.')
        instance.delete()

# 11. ShoppingList View
class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_personal = self.request.query_params.get('is_personal', None)
        queryset = ShoppingList.objects.filter(created_by=user).distinct()

        if is_personal == 'true':
            queryset = queryset.filter(is_personal=True)
        elif is_personal == 'false':
            queryset = queryset.filter(is_personal=False)
        return queryset

    def perform_create(self, serializer):
        is_personal = self.request.data.get('is_personal', False)
        group = serializer.validated_data.get('group')

        if is_personal and group:
            raise serializers.ValidationError("A personal list cannot belong to a group.")
        if not is_personal and not group:
            raise serializers.ValidationError("A group list must belong to a group.")

        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        shopping_list = self.get_object()
        serializer = ShoppingListItemsSerializer(data=request.data)
        if serializer.is_valid():
            ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                item=serializer.validated_data['item'],
                quantity=serializer.validated_data['quantity']
            )
            return Response({'status': 'Item added successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='update-item')
    def update_item(self, request, pk=None):
        shopping_list = self.get_object()
        data = request.data
        try:
            item = ShoppingListItem.objects.get(
                shopping_list=shopping_list,
                item_id=data['item_id']
            )
            item.quantity = data['quantity']
            item.save()
            return Response({'status': 'Item updated successfully.'}, status=status.HTTP_200_OK)
        except ShoppingListItem.DoesNotExist:
            return Response({'error': 'Item not found in this shopping list.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        shopping_list = self.get_object()
        data = request.data
        try:
            item = ShoppingListItem.objects.get(
                shopping_list=shopping_list,
                item_id=data['item_id']
            )
            item.delete()
            return Response({'status': 'Item removed successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except ShoppingListItem.DoesNotExist:
            return Response({'error': 'Item not found in this shopping list.'}, status=status.HTTP_404_NOT_FOUND)


# @TODO: Implement the following views, maybe combine with frontend view?:
# 12. User Registration with Invitation View


# 13. CustomViews for password reset process
class CustomPasswordResetView(PasswordResetView):
    template_name = "password_reset_form.html"
    success_url = '/web/api/selfservice/password-reset/done/'
    def form_valid(self, form):
        """
        Override form_valid to handle email-based password reset securely.
        """
        email = form.cleaned_data.get('email')
        # Check if email exists in the database
        users = User.objects.filter(email=email)
        if users.exists():
            for user in users:
                # Generate a password reset token
                token = default_token_generator.make_token(user)
                # Generate uid
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                # Call the mail service to send email
                send_password_reset_mail(user, token, uid)
        return redirect(self.success_url)
