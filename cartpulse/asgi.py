"""
ASGI entrypoint. Routes plain HTTP to Django as usual, and upgrades
`ws/...` connections to the Channels WebSocket consumers so clients get
live inventory + pricing pushes instead of having to poll the REST API.
"""
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cartpulse.settings")

django_asgi_app = get_asgi_application()

import inventory.routing  # noqa: E402  (must import after apps are loaded)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(inventory.routing.websocket_urlpatterns)
        ),
    }
)
