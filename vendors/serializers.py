from rest_framework import serializers

from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id", "username", "store_name", "slug",
            "commission_rate", "is_active", "rating", "created_at",
        ]
        read_only_fields = ["commission_rate", "rating", "created_at"]
