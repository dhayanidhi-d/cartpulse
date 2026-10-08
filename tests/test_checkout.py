import pytest
from rest_framework.test import APIClient

from inventory.models import InventoryItem
from orders.models import Order


@pytest.mark.django_db
def test_checkout_decrements_stock_and_creates_order(listing, inventory_item, buyer):
    client = APIClient()
    client.force_authenticate(user=buyer)

    resp = client.post(
        "/api/orders/checkout/",
        {"items": [{"listing_id": listing.id, "quantity": 3}]},
        format="json",
    )

    assert resp.status_code == 201
    assert Order.objects.filter(buyer=buyer).count() == 1

    inventory_item.refresh_from_db()
    assert inventory_item.quantity == 97  # started at 100


@pytest.mark.django_db
def test_checkout_rejects_overselling(listing, inventory_item, buyer):
    client = APIClient()
    client.force_authenticate(user=buyer)

    resp = client.post(
        "/api/orders/checkout/",
        {"items": [{"listing_id": listing.id, "quantity": 10_000}]},
        format="json",
    )

    assert resp.status_code == 400
    inventory_item.refresh_from_db()
    assert inventory_item.quantity == 100  # untouched — nothing should have been decremented
    assert Order.objects.count() == 0  # whole transaction rolled back, including the Order row
