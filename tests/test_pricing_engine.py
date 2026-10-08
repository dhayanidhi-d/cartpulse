from decimal import Decimal

import pytest

from pricing.engine import PricingEngine


@pytest.mark.django_db
def test_no_signal_means_no_price_change(listing, inventory_item):
    # 100 units vs reorder_threshold=20 -> ratio 5.0, between low(0.15) and overstock(3.0)... 
    # actually 5.0 > 3.0 so this WILL trigger overstock; adjust to a neutral ratio instead.
    inventory_item.quantity = 40  # ratio = 2.0 -> neutral zone
    inventory_item.save()

    decision = PricingEngine(listing).evaluate()

    assert decision.changed is False
    assert decision.new_price == listing.price


@pytest.mark.django_db
def test_low_stock_triggers_scarcity_markup(listing, inventory_item):
    inventory_item.quantity = 2  # ratio = 2/20 = 0.10 <= LOW_STOCK_RATIO (0.15)
    inventory_item.save()

    decision = PricingEngine(listing).evaluate()

    assert decision.changed is True
    assert decision.new_price > listing.base_price
    assert decision.new_price <= listing.max_price
    assert "low stock" in decision.reason_text


@pytest.mark.django_db
def test_overstock_triggers_clearance_discount(listing, inventory_item):
    inventory_item.quantity = 100  # ratio = 100/20 = 5.0 >= OVERSTOCK_RATIO (3.0)
    inventory_item.save()

    decision = PricingEngine(listing).evaluate()

    assert decision.changed is True
    assert decision.new_price < listing.base_price
    assert decision.new_price >= listing.min_price
    assert "overstock" in decision.reason_text


@pytest.mark.django_db
def test_price_never_breaks_vendor_band(listing, inventory_item):
    # Force an extreme scarcity scenario and confirm we still respect max_price.
    inventory_item.quantity = 0
    inventory_item.save()
    listing.max_price = Decimal("1005.00")  # a very tight ceiling just above base_price
    listing.save()

    decision = PricingEngine(listing).evaluate()

    assert decision.new_price <= listing.max_price
