from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from inventory.models import InventoryItem
from products.models import Category, Product, VendorListing
from vendors.models import Vendor

User = get_user_model()


@pytest.fixture
def vendor(db):
    user = User.objects.create_user(username="seller1", password="pass12345")
    return Vendor.objects.create(user=user, store_name="Test Store", slug="test-store")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics", slug="electronics")


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name="Wireless Earbuds", slug="wireless-earbuds", category=category, sku="SKU-001"
    )


@pytest.fixture
def listing(db, vendor, product):
    return VendorListing.objects.create(
        vendor=vendor,
        product=product,
        base_price=Decimal("1000.00"),
        price=Decimal("1000.00"),
        min_price=Decimal("800.00"),
        max_price=Decimal("1300.00"),
    )


@pytest.fixture
def inventory_item(db, listing):
    return InventoryItem.objects.create(listing=listing, quantity=100, reorder_threshold=20)


@pytest.fixture
def buyer(db):
    return User.objects.create_user(username="buyer1", password="pass12345")
