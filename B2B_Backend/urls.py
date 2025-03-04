"""
URL configuration for B2B_Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from Webshop.views import default_view

url_prefix = 'web'

# URL patterns for the project
urlpatterns = [
    path(f'{url_prefix}/', default_view),
    path(f'{url_prefix}/admin/', admin.site.urls),
    path(f'{url_prefix}/api/', include('Webshop.urls')),  # Include app's URLs under /api/
]
