from baton.autodiscover import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from marketAPI.views import UpdateUserAddressView, ProductView, PartnerUpdateView, OrderProductModelViewSet, \
    BasketProductViewSet, trigger_error

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r'basket', BasketProductViewSet, basename='basket')
router.register(r'orders', OrderProductModelViewSet, basename='orders')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('baton/', include("baton.urls")),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('lk/address/', UpdateUserAddressView.as_view(), name='update-user-address'),
    path('update/', PartnerUpdateView.as_view(), name='partner-update'),
    path('products/', ProductView.as_view(), name='product-list'),
    path('product/<int:pk>/', ProductView.as_view(), name='product-detail'),
    path('', include(router.urls)),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('sentry-debug/', trigger_error), # check sentry
]

urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
