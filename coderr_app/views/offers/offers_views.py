from rest_framework import generics, permissions, status, parsers, filters, pagination
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Min, Q
from django.db import transaction

from ...models import Offer, OfferDetail
from ...serializers.offers.offers_serializers import OfferDetailSerializer, OfferSerializer # Importiere Offer Serializers


class OfferPagination(pagination.PageNumberPagination):
    """
    Pagination class for offers.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

class OfferListView(generics.ListCreateAPIView):
    """
    View to list and create offers. Supports filtering, searching, and ordering.
    """
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    pagination_class = OfferPagination
    filter_backends = [filters.SearchFilter]
    ordering_fields = ['updated_at', 'min_price']
    search_fields = ['title', 'description']
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        """
        Determines permissions based on the request method (POST requires authentication).
        """
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        """
        Filters offers based on query parameters like creator_id, min_price, and max_delivery_time.
        """
        queryset = super().get_queryset()
        creator_id = self.request.query_params.get('creator_id')
        min_price = self.request.query_params.get('min_price')
        max_delivery_time = self.request.query_params.get('max_delivery_time')

        if creator_id:
            queryset = queryset.filter(user_id=creator_id)
        if min_price:
            queryset = queryset.filter(details__price__gte=min_price)

        if max_delivery_time:
            queryset = queryset.annotate(
                min_delivery_time_annotated=Min('details__delivery_time_in_days')
            ).filter(min_delivery_time_annotated__lte=max_delivery_time)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Lists offers with support for custom ordering by 'min_price' and 'updated_at'.
        Handles pagination and returns paginated results.
        """
        queryset = self.filter_queryset(self.get_queryset())

        ordering = request.query_params.get('ordering')
        if ordering == 'min_price':
            queryset = sorted(queryset, key=lambda offer: offer.min_price or float('inf'))
        elif ordering == '-min_price':
            queryset = sorted(queryset, key=lambda offer: offer.min_price or float('-inf'), reverse=True)
        elif ordering == 'updated_at':
            queryset = queryset.order_by('updated_at')
        elif ordering == '-updated_at':
             queryset = queryset.order_by('-updated_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        """
        Creates a new offer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        """
        Checks if the requesting user is the owner of the object.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user

class OfferDetailView(generics.RetrieveAPIView):
    """
    View to retrieve offer details.
    """
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [AllowAny]

class OfferDetailDeleteView(generics.RetrieveDestroyAPIView):
    """
    View to retrieve and delete offer details.
    """
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

class OfferUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, and delete offers.
    """
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def patch(self, request, *args, **kwargs):
        """
        Updates an existing offer, including offer details and image.
        Handles partial updates and image replacement.
        """
        instance = self.get_object()

        image_data = request.FILES.get('image')
        if image_data:
            instance.image = image_data
            instance.save(update_fields=['image'])

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        details_data = request.data.get('details')
        if details_data is not None:
            self.update_details(instance, details_data)

        self.perform_update(serializer)
        return Response(serializer.data)

    def update_details(self, offer, details_data):
        """
        Updates offer details, adding new ones, updating existing ones, and deleting removed ones.
        Uses atomic transactions to ensure data consistency.
        """
        existing_details = {detail.id: detail for detail in offer.details.all()}
        updated_detail_ids = []

        with transaction.atomic():
            for detail_data in details_data:
                detail_id = detail_data.get('id')

                if detail_id:
                    detail = existing_details.get(detail_id)
                    if detail:
                        serializer = OfferDetailSerializer(detail, data=detail_data, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        updated_detail_ids.append(detail_id)


                else:
                    serializer = OfferDetailSerializer(data=detail_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(offer=offer)


            for detail_id, detail in existing_details.items():
                if detail_id not in updated_detail_ids:
                    detail.delete()

    def perform_update(self, serializer):
        """
        Saves the updated serializer data.
        """
        serializer.save()

    def delete(self, request, *args, **kwargs):
        """
        Deletes an offer.
        """
        return self.destroy(request, *args, **kwargs)