import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer

INVENTORY_GROUP = "inventory_updates"


class InventoryConsumer(AsyncJsonWebsocketConsumer):
    """
    Clients connect to ws://.../ws/inventory/ and receive live JSON events
    whenever stock or price changes anywhere on the platform, e.g.:

        {"event": "inventory.update", "listing_id": 12, "available_quantity": 4}
        {"event": "pricing.update",   "listing_id": 12, "old_price": "499.00", "new_price": "549.00", "reason": "low_stock"}

    This replaces polling the REST API every few seconds — the client just
    listens, so a shopper sees "Only 2 left!" or a price change update in
    real time without refreshing.
    """

    async def connect(self):
        await self.channel_layer.group_add(INVENTORY_GROUP, self.channel_name)
        await self.accept()
        await self.send_json({"event": "connection.ack", "message": "subscribed to inventory_updates"})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(INVENTORY_GROUP, self.channel_name)

    # Called for group_send(..., {"type": "inventory_update", ...})
    async def inventory_update(self, event):
        await self.send_json(event["payload"])

    # Called for group_send(..., {"type": "pricing_update", ...})
    async def pricing_update(self, event):
        await self.send_json(event["payload"])
