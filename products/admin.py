from django.contrib import admin

from .models import Category, Product, VendorListing


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category")
    search_fields = ("name", "sku")


@admin.register(VendorListing)
class VendorListingAdmin(admin.ModelAdmin):
    list_display = ("product", "vendor", "price", "min_price", "max_price", "is_active")
    list_filter = ("is_active", "vendor")
