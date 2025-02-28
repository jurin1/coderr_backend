from django.urls import path, include
from .views.views import FileUploadView, BaseInfoView
from .views.profiles.profiles_views import (
    UserRegistrationView, 
    UserLoginView,
    ProfileDetailView,
)
from .views.offers.offers_views import OfferDetailView
from .views.orders.orders_views import OrderCountView, CompletedOrderCountView


urlpatterns = [
    path('registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='my-profile'), 
    path('profiles/', include('coderr_app.views.profiles.urls')), 
    path('offers/', include('coderr_app.views.offers.urls')),   
    path('offerdetails/<int:pk>/', OfferDetailView.as_view(), name='offerdetail-detail'), 
    path('order-count/<int:business_user_id>/', OrderCountView.as_view(), name='order-count'), 
    path('completed-order-count/<int:business_user_id>/', CompletedOrderCountView.as_view(), name='completed-order-count'),  
    path('orders/', include('coderr_app.views.orders.urls')),     
    path('reviews/', include('coderr_app.views.reviews.urls')),   
    path('upload/', FileUploadView.as_view(), name='file-upload'), 
    path('base-info/', BaseInfoView.as_view(), name='base-info'),   
]