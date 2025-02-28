from django.urls import path
from .reviews_views import (
    ReviewListCreateView,
    ReviewUpdateDestroyView,
)

urlpatterns = [
    path('', ReviewListCreateView.as_view(), name='review-list-create'),
    path('<int:pk>/', ReviewUpdateDestroyView.as_view(), name='review-update-destroy'),
]