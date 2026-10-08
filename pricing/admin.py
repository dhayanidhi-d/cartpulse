from django.contrib import admin

from .models import PriceHistory, PricingRule


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "rule_type", "weight", "is_active")


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("listing", "old_price", "new_price", "created_at")
    readonly_fields = ("listing", "old_price", "new_price", "reason", "created_at")
