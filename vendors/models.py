from django.conf import settings
from django.db import models


class Vendor(models.Model):
    """A seller on the marketplace. One Django user can own one vendor storefront."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor_profile"
    )
    store_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="Platform commission % taken on each sale.",
    )
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["store_name"]

    def __str__(self):
        return self.store_name
