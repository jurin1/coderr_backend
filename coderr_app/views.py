from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework import generics, permissions, status, parsers, filters, pagination, parsers
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Min
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
    ReviewSerializer,
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
    filter_backends = [filters.SearchFilter]
    ordering_fields = ['updated_at', 'min_price']
    search_fields = ['title', 'description']
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
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
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def patch(self, request, *args, **kwargs):
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
        try:
            order = super().get_object()
        except Order.DoesNotExist:
            return Response({"detail": "The specified order was not found."}, status=status.HTTP_404_NOT_FOUND)
        return order


    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if isinstance(order, Response):
            return order
        
        if request.user.type != "business" or request.user.id != order.business_user.id:
            return Response({"detail": "Only the assigned business user can update the status of this order."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            if 'status' in request.data:
                valid_status_values = ['in_progress', 'completed', 'cancelled'] 
                if request.data['status'] not in valid_status_values:
                    return Response({"detail": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                 return Response({"detail": "The 'status' field is missing in the request body."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, Response):
            return instance
        if not request.user.is_staff:
            return Response({"detail": "Only admin users are allowed to delete orders."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

    def handle_exception(self, exc):
        if isinstance(exc, Order.DoesNotExist):
            return Response({"detail": "The specified order was not found."}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)


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

    def update(self, request, *args, **kwargs):
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