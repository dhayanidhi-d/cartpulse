from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .broadcast import broadcast
from .models import InventoryItem


@receiver(post_save, sender=InventoryItem)
def on_inventory_change(sender, instance: InventoryItem, created, **kwargs):
    """
    Two things happen whenever stock changes (restock, sale, adjustment):
      1. Every connected client is told the new available quantity, live.
      2. The pricing engine is asked (async, via Celery) to re-evaluate this
         listing's price — e.g. stock running low can justify a scarcity
         markup, a big restock can trigger a clearance discount.

    Both run in `transaction.on_commit` so we never broadcast/recalculate
    based on a row that then gets rolled back.
    """

    def _after_commit():
        broadcast(
            "inventory_update",
            {
                "event": "inventory.update",
                "listing_id": instance.listing_id,
                "quantity": instance.quantity,
                "reserved_quantity": instance.reserved_quantity,
                "available_quantity": instance.available_quantity,
            },
        )
        from pricing.tasks import recalculate_price

        recalculate_price.delay(instance.listing_id)

    transaction.on_commit(_after_commit)
