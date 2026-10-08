from rest_framework import serializers

from products.models import VendorListing

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="listing.product.name", read_only=True)
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["id", "listing", "product_name", "quantity", "price_at_purchase", "line_total"]
        read_only_fields = ["price_at_purchase"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "buyer", "status", "total_amount", "items", "created_at"]
        read_only_fields = ["buyer", "status", "total_amount", "created_at"]


class CheckoutLineSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    """Input for POST /api/orders/checkout/ — a cart of (listing, quantity) pairs."""

    items = CheckoutLineSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Cart cannot be empty.")
        listing_ids = [i["listing_id"] for i in items]
        found = set(
            VendorListing.objects.filter(id__in=listing_ids, is_active=True).values_list("id", flat=True)
        )
        missing = set(listing_ids) - found
        if missing:
            raise serializers.ValidationError(f"Unknown or inactive listing ids: {sorted(missing)}")
        return items
