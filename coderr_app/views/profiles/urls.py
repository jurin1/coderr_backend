from django.urls import path
from .profiles_views import (
    BusinessProfileListView,
    CustomerProfileListView,
)

urlpatterns = [
    path('business/', BusinessProfileListView.as_view(), name='business-profile-list'),
    path('customer/', CustomerProfileListView.as_view(), name='customer-profile-list'),
]