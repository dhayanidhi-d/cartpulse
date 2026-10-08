from rest_framework import permissions, viewsets

from .models import Vendor
from .serializers import VendorSerializer


class VendorViewSet(viewsets.ModelViewSet):
    """
    list/retrieve are public (browse storefronts); create/update requires auth.
    A vendor can only edit their own storefront (see get_queryset + perform_create).
    """

    queryset = Vendor.objects.filter(is_active=True)
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
