from django.db import models

from products.models import VendorListing


class PricingRule(models.Model):
    """
    A configurable rule the engine applies. Kept data-driven (rather than
    hard-coded if/else) so business users could tune thresholds/weights from
    the admin without a code deploy — a common real-world requirement.
    """

    class RuleType(models.TextChoices):
        INVENTORY_BASED = "INVENTORY_BASED", "Inventory-based (scarcity / clearance)"
        DEMAND_BASED = "DEMAND_BASED", "Demand-based (recent order velocity)"
        COMPETITOR_BASED = "COMPETITOR_BASED", "Competitor-based (lowest rival price)"

    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    weight = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.0,
        help_text="Relative influence of this rule when several are active (0-1).",
    )
    is_active = models.BooleanField(default=True)
    config = models.JSONField(
        default=dict, blank=True,
        help_text="Optional per-rule overrides, e.g. {'max_markup_percent': 15}",
    )

    class Meta:
        ordering = ["-weight"]

    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class PriceHistory(models.Model):
    """Every price the engine (or a vendor) has ever set — powers price
    charts and 'why did my price change' debugging."""

    listing = models.ForeignKey(VendorListing, on_delete=models.CASCADE, related_name="price_history")
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "price histories"

    def __str__(self):
        return f"{self.listing} {self.old_price} -> {self.new_price}"
