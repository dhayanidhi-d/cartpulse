import logging

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def recalculate_price(self, listing_id: int):
    """
    Triggered:
      - immediately after any inventory change (inventory/signals.py), and
      - periodically for every active listing (see recalculate_all_prices,
        wire it up in django-celery-beat / crontab for e.g. every 15 min)
        to catch demand-based drift even when stock hasn't moved.
    """
    from products.models import VendorListing

    from .engine import PricingEngine
    from .models import PriceHistory

    try:
        listing = VendorListing.objects.select_related("inventory_item").get(
            pk=listing_id, is_active=True
        )
    except VendorListing.DoesNotExist:
        return

    decision = PricingEngine(listing).evaluate()
    if not decision.changed:
        return

    with transaction.atomic():
        listing.price = decision.new_price
        listing.save(update_fields=["price", "updated_at"])
        PriceHistory.objects.create(
            listing=listing,
            old_price=decision.old_price,
            new_price=decision.new_price,
            reason=decision.reason_text,
        )

    from inventory.broadcast import broadcast

    broadcast(
        "pricing_update",
        {
            "event": "pricing.update",
            "listing_id": listing.id,
            "old_price": str(decision.old_price),
            "new_price": str(decision.new_price),
            "reason": decision.reason_text,
        },
    )
    logger.info("Repriced listing %s: %s", listing_id, decision.reason_text)


@shared_task
def recalculate_all_prices():
    """Periodic sweep — schedule via django-celery-beat, e.g. every 15 minutes."""
    from products.models import VendorListing

    ids = list(VendorListing.objects.filter(is_active=True).values_list("id", flat=True))
    for listing_id in ids:
        recalculate_price.delay(listing_id)
    return f"queued repricing for {len(ids)} listings"
