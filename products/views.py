from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import Category, Product, VendorListing
from .serializers import CategorySerializer, ProductSerializer, VendorListingSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    """
    Public product catalog. Supports ?category=<id> and ?search=<name>
    so the frontend can build filterable listing pages cheaply.
    """

    queryset = Product.objects.select_related("category").prefetch_related(
        "listings", "listings__vendor", "listings__inventory_item"
    )
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category"]
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["name", "created_at"]


class VendorListingViewSet(viewsets.ModelViewSet):
    """
    A vendor manages their own listings (price/min/max) here. Actual stock
    quantities live in the `inventory` app, not here — keeps pricing rules
    and stock-keeping cleanly separated.
    """

    queryset = VendorListing.objects.select_related("vendor", "product", "inventory_item")
    serializer_class = VendorListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["vendor", "product", "is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true" and self.request.user.is_authenticated:
            qs = qs.filter(vendor__user=self.request.user)
        return qs
