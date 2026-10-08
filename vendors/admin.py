from django.contrib import admin

from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("store_name", "user", "is_active", "commission_rate", "rating")
    search_fields = ("store_name", "user__username")
    list_filter = ("is_active",)
