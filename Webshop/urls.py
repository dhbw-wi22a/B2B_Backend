# Webshop/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, ItemViewSet, UserRegistrationView

router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'users', UserRegistrationView, basename='users')

urlpatterns = [
    path('', include(router.urls)),  # Register all API routes
]
