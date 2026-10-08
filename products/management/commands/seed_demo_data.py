from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import InventoryItem
from products.models import Category, Product, VendorListing
from vendors.models import Vendor

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo vendors, products and stock — great for a live interview demo."

    @transaction.atomic
    def handle(self, *args, **options):
        electronics, _ = Category.objects.get_or_create(name="Electronics", defaults={"slug": "electronics"})
        home, _ = Category.objects.get_or_create(name="Home & Kitchen", defaults={"slug": "home-kitchen"})

        vendors_data = [
            ("techbazaar", "TechBazaar"),
            ("homehaven", "HomeHaven Store"),
        ]
        vendors = []
        for username, store_name in vendors_data:
            user, _ = User.objects.get_or_create(username=username, defaults={"email": f"{username}@example.com"})
            user.set_password("demopass123")
            user.save()
            vendor, _ = Vendor.objects.get_or_create(
                user=user, defaults={"store_name": store_name, "slug": username}
            )
            vendors.append(vendor)

        products_data = [
            ("Wireless Earbuds Pro", "wireless-earbuds-pro", "SKU-EARBUDS-01", electronics, 2500, 5),
            ("Smart LED Bulb (4-pack)", "smart-led-bulb-4pack", "SKU-BULB-01", home, 999, 60),
            ("Mechanical Keyboard", "mechanical-keyboard", "SKU-KEYB-01", electronics, 3200, 15),
        ]

        for name, slug, sku, category, base_price, stock in products_data:
            product, _ = Product.objects.get_or_create(
                sku=sku, defaults={"name": name, "slug": slug, "category": category}
            )
            for vendor in vendors:
                listing, created = VendorListing.objects.get_or_create(
                    vendor=vendor,
                    product=product,
                    defaults={
                        "base_price": Decimal(base_price),
                        "price": Decimal(base_price),
                        "min_price": Decimal(base_price) * Decimal("0.75"),
                        "max_price": Decimal(base_price) * Decimal("1.25"),
                    },
                )
                if created:
                    InventoryItem.objects.create(
                        listing=listing, quantity=stock, reorder_threshold=max(stock // 5, 5)
                    )

        self.stdout.write(self.style.SUCCESS(
            "Seeded 2 vendors, 3 products, 6 vendor listings + starting stock. "
            "Login as 'techbazaar' / 'homehaven' with password 'demopass123'."
        ))
