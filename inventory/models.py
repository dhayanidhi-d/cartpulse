from django.db import models

from products.models import VendorListing


class InventoryItem(models.Model):
    """Live stock for one vendor's listing. Kept separate from VendorListing
    so stock can be updated at high frequency without touching pricing rows."""

    listing = models.OneToOneField(
        VendorListing, on_delete=models.CASCADE, related_name="inventory_item"
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(
        default=0, help_text="Held for orders in checkout but not yet confirmed."
    )
    reorder_threshold = models.PositiveIntegerField(
        default=10, help_text="Below this, the pricing engine treats stock as 'low'."
    )
    warehouse_location = models.CharField(max_length=120, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_quantity(self):
        return max(self.quantity - self.reserved_quantity, 0)

    def __str__(self):
        return f"{self.listing} — {self.quantity} in stock"


class InventoryLog(models.Model):
    """Immutable audit trail of every stock movement. This is what makes
    'why did this go out of stock / why did the price change' answerable."""

    class Reason(models.TextChoices):
        RESTOCK = "RESTOCK", "Restock"
        SALE = "SALE", "Sale"
        RESERVATION = "RESERVATION", "Reservation"
        RELEASE = "RELEASE", "Reservation released"
        ADJUSTMENT = "ADJUSTMENT", "Manual adjustment"

    listing = models.ForeignKey(
        VendorListing, on_delete=models.CASCADE, related_name="inventory_logs"
    )
    change_qty = models.IntegerField(help_text="Positive = added to stock, negative = removed.")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.listing} {self.change_qty:+d} ({self.reason})"
