from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PriceHistory, PricingRule
from .serializers import PriceHistorySerializer, PricingRuleSerializer


class PricingRuleViewSet(viewsets.ModelViewSet):
    queryset = PricingRule.objects.all()
    serializer_class = PricingRuleSerializer
    permission_classes = [permissions.IsAdminUser]


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PriceHistory.objects.select_related("listing", "listing__product")
    serializer_class = PriceHistorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["listing"]

    @action(detail=False, methods=["post"], url_path="recalculate/(?P<listing_id>[^/.]+)")
    def recalculate(self, request, listing_id=None):
        """Manual trigger — handy for demos: POST /api/pricing/history/recalculate/5/"""
        from .tasks import recalculate_price

        recalculate_price.delay(int(listing_id))
        return Response({"detail": f"Repricing queued for listing {listing_id}."}, status=202)
