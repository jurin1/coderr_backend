from django.urls import path
from .offers_views import (
    OfferListView,
    OfferUpdateView,
)

urlpatterns = [
    path('', OfferListView.as_view(), name='offer-list'),
    path('<int:pk>/', OfferUpdateView.as_view(), name='offer-update'),
]