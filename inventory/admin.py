from django.contrib import admin

from .models import InventoryItem, InventoryLog


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("listing", "quantity", "reserved_quantity", "reorder_threshold", "updated_at")


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("listing", "change_qty", "reason", "created_at")
    list_filter = ("reason",)
