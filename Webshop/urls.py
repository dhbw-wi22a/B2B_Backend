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
    AddressViewSet
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
]
