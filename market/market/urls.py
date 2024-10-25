"""
URL configuration for market project.

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
from rest_framework.routers import DefaultRouter

from marketAPI.views import UpdateUserAddressView, ProductView, PartnerUpdateView, OrderProductModelViewSet, \
    BasketProductViewSet

router = DefaultRouter()
router.register(r'basket', BasketProductViewSet, basename='basket')
router.register(r'orders', OrderProductModelViewSet, basename='orders')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('lk/address/', UpdateUserAddressView.as_view(), name='update-user-address'),
    path('update/', PartnerUpdateView.as_view(), name='partner-update'),
    path('products/', ProductView.as_view(), name='product-list'),
    path('product/<int:pk>/', ProductView.as_view(), name='product-detail'),
    path('', include(router.urls)),
]
