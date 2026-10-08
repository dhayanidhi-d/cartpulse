from rest_framework.routers import DefaultRouter

from .views import InventoryItemViewSet, InventoryLogViewSet

router = DefaultRouter()
router.register("items", InventoryItemViewSet, basename="inventory-item")
router.register("logs", InventoryLogViewSet, basename="inventory-log")

urlpatterns = router.urls
