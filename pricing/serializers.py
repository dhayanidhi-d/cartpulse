from rest_framework import serializers

from .models import PriceHistory, PricingRule


class PricingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingRule
        fields = ["id", "name", "rule_type", "weight", "is_active", "config"]


class PriceHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="listing.product.name", read_only=True)

    class Meta:
        model = PriceHistory
        fields = ["id", "listing", "product_name", "old_price", "new_price", "reason", "created_at"]
