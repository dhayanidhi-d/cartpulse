from rest_framework import serializers

from .models import Category, Product, VendorListing


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class VendorListingSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.store_name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = VendorListing
        fields = [
            "id", "vendor", "vendor_name", "product", "product_name",
            "base_price", "price", "min_price", "max_price", "is_active",
            "in_stock", "updated_at",
        ]
        read_only_fields = ["price", "updated_at"]  # `price` is engine-managed, not client-settable

    def get_in_stock(self, obj):
        item = getattr(obj, "inventory_item", None)
        return bool(item and item.available_quantity > 0)

    def validate(self, attrs):
        min_price = attrs.get("min_price", getattr(self.instance, "min_price", None))
        max_price = attrs.get("max_price", getattr(self.instance, "max_price", None))
        base_price = attrs.get("base_price", getattr(self.instance, "base_price", None))
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError("min_price cannot be greater than max_price.")
        if base_price is not None and min_price is not None and max_price is not None:
            if not (min_price <= base_price <= max_price):
                raise serializers.ValidationError("base_price must sit between min_price and max_price.")
        return attrs

    def create(self, validated_data):
        # Live price starts equal to the vendor's base price; the pricing
        # engine takes it from there as stock/demand signals come in.
        validated_data["price"] = validated_data["base_price"]
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), write_only=True
    )
    listings = VendorListingSerializer(many=True, read_only=True)
    best_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "sku",
            "category", "category_id", "listings", "best_price", "created_at",
        ]

    def get_best_price(self, obj):
        active = [l for l in obj.listings.all() if l.is_active]
        return min((l.price for l in active), default=None)
