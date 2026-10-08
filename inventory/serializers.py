from rest_framework import serializers

from .models import InventoryItem, InventoryLog


class InventoryItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.ReadOnlyField()
    product_name = serializers.CharField(source="listing.product.name", read_only=True)
    vendor_name = serializers.CharField(source="listing.vendor.store_name", read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id", "listing", "product_name", "vendor_name",
            "quantity", "reserved_quantity", "available_quantity",
            "reorder_threshold", "warehouse_location", "updated_at",
        ]
        read_only_fields = ["updated_at"]


class StockAdjustmentSerializer(serializers.Serializer):
    """Input shape for the `adjust-stock` action — never let clients set
    `quantity` directly, always route through here so an InventoryLog row
    is always created and the delta is auditable."""

    change_qty = serializers.IntegerField(help_text="Positive to add stock, negative to remove.")
    reason = serializers.ChoiceField(choices=InventoryLog.Reason.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, attrs):
        if attrs["change_qty"] == 0:
            raise serializers.ValidationError("change_qty cannot be zero.")
        return attrs


class InventoryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLog
        fields = ["id", "listing", "change_qty", "reason", "note", "created_at"]
