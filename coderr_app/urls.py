from django.urls import path
from .views import (
    UserRegistrationView, 
    UserLoginView, 
    ProfileDetailView, 
    FileUploadView, 
    BusinessProfileListView, 
    CustomerProfileListView,
    OfferDetailView,
    OfferListView,
    OfferUpdateView,
    OrderListCreateView,
    OrderUpdateDestroyView,
    OrderCountView,
    CompletedOrderCountView,
)

urlpatterns = [
    path('registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='business-profile-list'),
    path('profiles/customer/', CustomerProfileListView.as_view(), name='customer-profile-list'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('offers/', OfferListView.as_view(), name='offer-list'),
    path('offers/<int:pk>/', OfferUpdateView.as_view(), name='offer-update'), 
    path('offerdetails/<int:pk>/', OfferDetailView.as_view(), name='offerdetail-detail'),
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderUpdateDestroyView.as_view(), name='order-update-destroy'),
    path('order-count/<int:business_user_id>/', OrderCountView.as_view(), name='order-count'),
    path('completed-order-count/<int:business_user_id>/', CompletedOrderCountView.as_view(), name='completed-order-count'),
]