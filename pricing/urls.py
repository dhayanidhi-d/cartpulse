from rest_framework.routers import DefaultRouter

from .views import PriceHistoryViewSet, PricingRuleViewSet

router = DefaultRouter()
router.register("rules", PricingRuleViewSet, basename="pricing-rule")
router.register("history", PriceHistoryViewSet, basename="price-history")

urlpatterns = router.urls
