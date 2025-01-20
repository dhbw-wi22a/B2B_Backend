from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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

schema_view = get_schema_view(
    openapi.Info(
        title="B2B API",
        default_version='v1',
        description="API documentation for B2B Webshop",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="your_email@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
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
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
