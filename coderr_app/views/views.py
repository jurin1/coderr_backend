from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from ..models import FileUpload, Review, CustomUser, Offer
from ..serializers.serializers import FileUploadSerializer
from django.db.models import Avg
from rest_framework.parsers import MultiPartParser, FormParser

class FileUploadView(generics.CreateAPIView):
    """
    View for uploading files.
    """
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

class BaseInfoView(APIView):
    """
    View to retrieve base information like review counts, average rating, etc.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Retrieves and returns base information about the application, including review count, average rating,
        business profile count, and offer count.
        """
        review_count = Review.objects.count()
        average_rating = Review.objects.aggregate(Avg('rating'))['rating__avg']
        business_profile_count = CustomUser.objects.filter(type='business').count()
        offer_count = Offer.objects.count()

        if average_rating is not None:
            average_rating = round(average_rating, 1)
        else:
            average_rating = 0

        data = {
            'review_count': review_count,
            'average_rating': average_rating,
            'business_profile_count': business_profile_count,
            'offer_count': offer_count,
        }

        return Response(data, status=status.HTTP_200_OK)