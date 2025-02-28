from rest_framework import generics, permissions, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import Review
from ...serializers.reviews.reviews_serializers import ReviewSerializer 

class IsReviewerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow reviewers of a review to edit it.
    """
    def has_object_permission(self, request, view, obj):
        """
        Checks if the requesting user is the reviewer of the review object.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.reviewer == request.user

class ReviewListCreateView(generics.ListCreateAPIView):
    """
    View to list and create reviews. Supports filtering and ordering.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at', 'rating']

    def get_queryset(self):
        """
        Filters reviews based on query parameters like business_user_id and reviewer_id.
        """
        queryset = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        return queryset

    def perform_create(self, serializer):
        """
        Saves a new review, automatically setting the reviewer to the current user.
        """
        serializer.save(reviewer=self.request.user)

class ReviewUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, and delete reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewerOrReadOnly]

    def update(self, request, *args, **kwargs):
        """
        Updates an existing review, validating the request data and handling invalid keys.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)


        valid_keys = {'rating', 'description'}
        request_keys = set(request.data.keys())
        invalid_keys = request_keys - valid_keys

        if invalid_keys:
            return Response({"detail": "Bad Request. The request body contains invalid data."}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        """
        Saves the updated review data.
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        Deletes a review instance.
        """
        instance.delete()