from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import InventoryItem, InventoryLog
from .serializers import (
    InventoryItemSerializer,
    InventoryLogSerializer,
    StockAdjustmentSerializer,
)


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related("listing", "listing__product", "listing__vendor")
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["listing"]

    @action(detail=True, methods=["post"], url_path="adjust-stock")
    def adjust_stock(self, request, pk=None):
        """
        POST /api/inventory/items/{id}/adjust-stock/
        {"change_qty": -3, "reason": "SALE", "note": "order #452"}

        Uses select_for_update so concurrent sales on the same listing can't
        both read stale stock and oversell it (classic race condition).
        """
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_qty = serializer.validated_data["change_qty"]
        reason = serializer.validated_data["reason"]
        note = serializer.validated_data.get("note", "")

        with transaction.atomic():
            item = get_object_or_404(InventoryItem.objects.select_for_update(), pk=pk)
            new_quantity = item.quantity + change_qty
            if new_quantity < 0:
                return Response(
                    {"detail": "Adjustment would make stock negative."}, status=400
                )
            item.quantity = new_quantity
            item.save(update_fields=["quantity", "updated_at"])
            InventoryLog.objects.create(
                listing=item.listing, change_qty=change_qty, reason=reason, note=note
            )

        return Response(InventoryItemSerializer(item).data)


class InventoryLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryLog.objects.select_related("listing")
    serializer_class = InventoryLogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["listing", "reason"]
