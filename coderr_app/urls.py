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
]