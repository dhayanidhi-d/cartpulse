"""
The dynamic pricing engine.

Kept as plain, dependency-injectable Python (no Celery/Django-request
coupling) so it's trivially unit-testable — see tests/test_pricing_engine.py.
Celery (pricing/tasks.py) is just a thin wrapper that calls this and saves
the result.

Signals combined (each can be tuned/disabled via settings.PRICING_ENGINE or
a PricingRule row without touching this code):

  1. Inventory-based:  low stock -> scarcity markup, overstock -> clearance discount.
  2. Demand-based:      a burst of recent orders -> demand markup.

Everything is clamped to the vendor's own [min_price, max_price] band, so
the vendor is always in ultimate control of the acceptable price range —
the engine only decides *where* within that band to sit.
"""
from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

TWO_PLACES = Decimal("0.01")


@dataclass
class PricingDecision:
    new_price: Decimal
    old_price: Decimal
    reasons: list

    @property
    def changed(self) -> bool:
        return self.new_price != self.old_price

    @property
    def reason_text(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "no adjustment"


class PricingEngine:
    def __init__(self, listing, config=None):
        self.listing = listing
        self.config = config or settings.PRICING_ENGINE

    def _inventory_multiplier(self):
        """Returns (multiplier_delta, reason|None) from stock levels."""
        item = getattr(self.listing, "inventory_item", None)
        if item is None or item.reorder_threshold == 0:
            return Decimal("0"), None

        ratio = Decimal(item.available_quantity) / Decimal(item.reorder_threshold)
        low_ratio = Decimal(str(self.config["LOW_STOCK_RATIO"]))
        overstock_ratio = Decimal(str(self.config["OVERSTOCK_RATIO"]))
        max_markup = Decimal(str(self.config["MAX_MARKUP_PERCENT"])) / 100
        max_discount = Decimal(str(self.config["MAX_DISCOUNT_PERCENT"])) / 100

        if ratio <= low_ratio:
            # The scarcer the stock (ratio -> 0), the closer we push to the max markup.
            severity = Decimal("1") - min(ratio / low_ratio, Decimal("1")) if low_ratio else Decimal("1")
            delta = max_markup * severity
            return delta, f"low stock ({item.available_quantity} left) -> +{(delta * 100):.1f}% scarcity markup"

        if ratio >= overstock_ratio:
            severity = min((ratio - overstock_ratio) / overstock_ratio, Decimal("1"))
            delta = -(max_discount * severity)
            return delta, f"overstock ({item.available_quantity} units) -> {(delta * 100):.1f}% clearance discount"

        return Decimal("0"), None

    def _demand_multiplier(self):
        """Returns (multiplier_delta, reason|None) from recent order velocity."""
        from orders.models import OrderItem  # local import avoids app load-order coupling

        window_hours = self.config["DEMAND_WINDOW_HOURS"]
        since = timezone.now() - timedelta(hours=window_hours)
        recent_count = OrderItem.objects.filter(
            listing=self.listing, order__created_at__gte=since
        ).count()

        threshold = self.config["HIGH_DEMAND_ORDER_COUNT"]
        if recent_count >= threshold:
            # Cap the demand bump at half of the max markup, so a demand spike
            # combined with low stock can't blow past MAX_MARKUP_PERCENT alone.
            max_markup = Decimal(str(self.config["MAX_MARKUP_PERCENT"])) / 100
            delta = min(max_markup / 2, max_markup / 2 * (Decimal(recent_count) / threshold))
            return delta, f"high demand ({recent_count} orders in {window_hours}h) -> +{(delta * 100):.1f}% demand markup"

        return Decimal("0"), None

    def evaluate(self) -> PricingDecision:
        old_price = self.listing.price
        base_price = self.listing.base_price

        total_delta = Decimal("0")
        reasons = []

        for delta, reason in (self._inventory_multiplier(), self._demand_multiplier()):
            if reason:
                total_delta += delta
                reasons.append(reason)

        multiplier = Decimal("1") + total_delta
        candidate = (base_price * multiplier).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Vendor-set floor/ceiling always wins — the engine nudges within the band.
        clamped = min(max(candidate, self.listing.min_price), self.listing.max_price)
        if clamped != candidate:
            reasons.append(f"clamped to vendor band [{self.listing.min_price}, {self.listing.max_price}]")

        return PricingDecision(new_price=clamped, old_price=old_price, reasons=reasons)
