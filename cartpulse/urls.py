from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/vendors/", include("vendors.urls")),
    path("api/catalog/", include("products.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/pricing/", include("pricing.urls")),
    path("api/orders/", include("orders.urls")),
]
