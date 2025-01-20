from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    OrderViewSet,
    ItemViewSet,
    UserRegistrationView,
    UserView,
    UserShortView,
    ShoppingCartViewSet,
    AddressViewSet,
    EmailVerificationView,
    CompanyGroupViewSet,
    CompanyGroupMembershipViewSet,
    GroupInvitationViewSet,
    ShoppingListViewSet,
)

# Register ViewSets with the router
router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='items')

# Create a separate router for 'me/' endpoints
me_router = DefaultRouter()
me_router.register(r'detail', UserView, basename='my-full-profile')
me_router.register(r'orders', OrderViewSet, basename='my-orders')
me_router.register(r'shopping-cart', ShoppingCartViewSet, basename='my-shoppingcart')
me_router.register(r'addresses', AddressViewSet, basename='my-addresses')
me_router.register(r'profile', UserShortView, basename='my-profile')

# Seperate router for company group related endpoints
group_router = DefaultRouter()
group_router.register(r'groups', CompanyGroupViewSet, basename='company-groups')
group_router.register(r'invitations', GroupInvitationViewSet, basename='group-invitations')
group_router.register(r'memberships', CompanyGroupMembershipViewSet, basename='group-memberships')
group_router.register(r'shoppinglist', ShoppingListViewSet, basename='group-shoppinglist')

# Add URLs for accept and decline endpoints for group invitations
group_invitation_patterns = [
    path('invitations/<uuid:token>/accept/', GroupInvitationViewSet.as_view({'get': 'accept_invitation'}), name='group-invitation-accept'),
    path('invitations/<uuid:token>/decline/', GroupInvitationViewSet.as_view({'get': 'decline_invitation'}), name='group-invitation-decline'),
]

# Auth URL patterns
auth_patterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# Main urlpatterns
urlpatterns = [
    path('', include(router.urls)),  # Include general ViewSet routes
    path('api-auth/', include('rest_framework.urls')),  # Enables login in the DRF UI
    path('auth/', include((auth_patterns, 'auth'), namespace='auth')),  # Grouped auth routes
    path('me/', include(me_router.urls)),  # Group all 'me/' routes under a single prefix
    path('verify-email/<uuid:token>/', EmailVerificationView.as_view({'get':'verify_email'}), name="verify-email"),
    path('group/', include(group_router.urls)),  # Include the group router
    path('group/', include(group_invitation_patterns)),  # Include invitation-specific patterns
]
