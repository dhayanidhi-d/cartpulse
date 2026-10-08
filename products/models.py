from django.db import models

from vendors.models import Vendor


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Master catalog entry shared across vendors, e.g. 'Samsung Galaxy Buds 2'.
    Multiple vendors can each sell the *same* Product at their own price/stock
    via VendorListing — that's the "multi-vendor" part of the platform.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    sku = models.CharField(max_length=64, unique=True, help_text="Global catalog SKU")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class VendorListing(models.Model):
    """One vendor's offer of one Product: their price, and a link point for stock."""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="listings")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="listings")

    base_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Vendor's own listed price — the anchor the pricing engine adjusts from.",
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Current live price shown to shoppers (base_price adjusted by the pricing engine).",
    )
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Floor price — the pricing engine will never discount below this.",
    )
    max_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Ceiling price — the pricing engine will never mark up above this.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("vendor", "product")
        ordering = ["price"]

    def __str__(self):
        return f"{self.product.name} @ {self.vendor.store_name} (₹{self.price})"
