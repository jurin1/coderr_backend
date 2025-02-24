from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ProfileSerializer, FileUploadSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions, status, parsers
from django.shortcuts import get_object_or_404
from .models import Profile, FileUpload

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