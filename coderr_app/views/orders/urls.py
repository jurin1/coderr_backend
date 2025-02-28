from django.urls import path
from .orders_views import (
    OrderListCreateView,
    OrderUpdateDestroyView,
)

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderUpdateDestroyView.as_view(), name='order-update-destroy'),
    
]