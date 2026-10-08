"""Settings used only under pytest — fast, hermetic, no external services."""
import os

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "True")
os.environ.setdefault("CHANNELS_USE_INMEMORY", "True")

from .settings import *  # noqa: F401,F403,E402

CELERY_TASK_ALWAYS_EAGER = True
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # faster test user creation
