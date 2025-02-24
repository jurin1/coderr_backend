from django.urls import path
from .views import UserRegistrationView, UserLoginView, ProfileDetailView, FileUploadView

urlpatterns = [
    path('registration/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]