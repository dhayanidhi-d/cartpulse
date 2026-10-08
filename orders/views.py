from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from inventory.models import InventoryItem, InventoryLog
from products.models import VendorListing

from .models import Order, OrderItem
from .serializers import CheckoutSerializer, OrderSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Buyers see only their own orders."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).prefetch_related("items")

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        """
        POST /api/orders/checkout/
        {"items": [{"listing_id": 3, "quantity": 2}, {"listing_id": 7, "quantity": 1}]}

        The whole cart is one atomic transaction: every line is stock-checked
        and decremented under a row lock (select_for_update) before the order
        is confirmed, so two shoppers racing for the last unit can't both win.
        Saving each InventoryItem re-fires the inventory signal, which pushes
        a live WebSocket update and asks the pricing engine to re-evaluate —
        so a single checkout can ripple into a real-time price change.
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines = serializer.validated_data["items"]

        with transaction.atomic():
            order = Order.objects.create(buyer=request.user, status=Order.Status.PENDING)
            total = 0

            for line in lines:
                listing = VendorListing.objects.select_related("inventory_item").get(
                    pk=line["listing_id"]
                )
                item = InventoryItem.objects.select_for_update().get(listing=listing)

                if item.available_quantity < line["quantity"]:
                    transaction.set_rollback(True)
                    return Response(
                        {"detail": f"Not enough stock for '{listing.product.name}' "
                                   f"(have {item.available_quantity}, wanted {line['quantity']})."},
                        status=400,
                    )

                item.quantity -= line["quantity"]
                item.save(update_fields=["quantity", "updated_at"])  # fires signal -> broadcast + repricing
                InventoryLog.objects.create(
                    listing=listing,
                    change_qty=-line["quantity"],
                    reason=InventoryLog.Reason.SALE,
                    note=f"order pending #{order.id}",
                )

                OrderItem.objects.create(
                    order=order,
                    listing=listing,
                    quantity=line["quantity"],
                    price_at_purchase=listing.price,
                )
                total += listing.price * line["quantity"]

            order.total_amount = total
            order.status = Order.Status.PAID  # demo: assume payment succeeds synchronously
            order.save(update_fields=["total_amount", "status"])

        return Response(OrderSerializer(order).data, status=201)
