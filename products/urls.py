from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet, VendorListingViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("listings", VendorListingViewSet, basename="listing")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
