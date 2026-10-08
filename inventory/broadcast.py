"""
Small helper module so both `inventory` and `pricing` apps can push a
WebSocket event without duplicating the channel-layer boilerplate.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .consumers import INVENTORY_GROUP


def broadcast(event_type: str, payload: dict):
    """
    event_type: 'inventory_update' or 'pricing_update' (matches the consumer
    method names). Safe to call even if no channel layer / Redis is running
    in a given environment (e.g. simple unit tests) — it fails silently.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            INVENTORY_GROUP, {"type": event_type, "payload": payload}
        )
    except Exception as e:
        print("BROADCAST ERROR:", repr(e))