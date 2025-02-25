from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework import generics, permissions, status, parsers, filters, pagination
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Avg
from django.db import transaction
from .models import Profile, FileUpload, Offer, OfferDetail, CustomUser, Order, Review
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    ProfileSerializer,
    FileUploadSerializer,
    BusinessProfileSerializer,
    CustomerProfileSerializer,
    OfferDetailSerializer,
    OfferSerializer,
    OrderSerializer,
    OrderCountSerializer,
    CompletedOrderCountSerializer,
    ReviewSerializer
)

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.save()
            return Response({
                "token": user_data['token'],
                "username": user_data['username'],
                "email": user_data['email'],
                "user_id": user_data['user_id']
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserLoginView(APIView): 
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_data = UserRegistrationSerializer().get_user_data(user) 
            return Response(user_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class ProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user_id=self.kwargs['pk'])


    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        if request.user != profile.user:
            return Response({"detail": "You do not have permission to update this profile."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().patch(request, *args, **kwargs)
    
class FileUploadView(generics.CreateAPIView):
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

class BaseProfileListView(generics.ListAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None 

    def get_queryset(self):
        if self.user_type is None:
            raise NotImplementedError("user_type must be set in subclasses.")
        return Profile.objects.filter(user__type=self.user_type)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)
        return Response(serializer.data)

class BusinessProfileListView(BaseProfileListView):
    serializer_class = BusinessProfileSerializer 
    user_type = 'business'

class CustomerProfileListView(BaseProfileListView):
    serializer_class = CustomerProfileSerializer 
    user_type = 'customer'

class OfferPagination(pagination.PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 1000

class OfferListView(generics.ListCreateAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    pagination_class = OfferPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['updated_at', 'min_price']
    search_fields = ['title', 'description']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class IsOwnerOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user
class OfferDetailView(generics.RetrieveAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [AllowAny]  

class OfferDetailDeleteView(generics.RetrieveDestroyAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

class OfferUpdateView(generics.RetrieveUpdateDestroyAPIView): 
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        
        details_data = request.data.get('details')
        if details_data is not None:  
            self.update_details(instance, details_data)

        self.perform_update(serializer)
        return Response(serializer.data)

    def update_details(self, offer, details_data):
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
        serializer.save()

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class OrderUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        order = super().get_object()
        if self.request.method == 'PATCH':
          if self.request.user.type != "business":
            raise PermissionError("Only business users can update the order status.")
        if self.request.method == 'DELETE':
            if not self.request.user.is_staff:
                raise PermissionError("Only admin users can delete orders.")
        return order

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        instance.delete()


class OrderCountView(generics.RetrieveAPIView):
    serializer_class = OrderCountSerializer
    permission_classes = [AllowAny] 
    def get(self, request, *args, **kwargs):
        business_user_id = self.kwargs['business_user_id']
        get_object_or_404(CustomUser, id=business_user_id, type='business')  

        order_count = Order.objects.filter(business_user_id=business_user_id, status='in_progress').count()
        serializer = self.get_serializer({'order_count': order_count})
        return Response(serializer.data)


class CompletedOrderCountView(generics.RetrieveAPIView):
    serializer_class = CompletedOrderCountSerializer
    permission_classes = [AllowAny] 

    def get(self, request, *args, **kwargs):
        business_user_id = self.kwargs['business_user_id']
        get_object_or_404(CustomUser, id=business_user_id, type='business') 

        completed_order_count = Order.objects.filter(business_user_id=business_user_id, status='completed').count()
        serializer = self.get_serializer({'completed_order_count': completed_order_count})
        return Response(serializer.data)
    
class IsReviewerOrReadOnly(permissions.BasePermission):
    """
    Benutzerdefinierte Berechtigung, die nur dem Ersteller einer Bewertung erlaubt, sie zu bearbeiten oder zu löschen.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.reviewer == request.user

class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated] 
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at', 'rating']

    def get_queryset(self):
        queryset = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

class ReviewUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewerOrReadOnly]  

    def perform_update(self, serializer):
        serializer.save()
    
    def perform_destroy(self, instance):
        instance.delete()

class BaseInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
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