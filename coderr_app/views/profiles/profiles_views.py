from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import generics, permissions, status
from django.shortcuts import get_object_or_404
from ...models import Profile
from ...serializers.profiles.profile_serializers import ( 
    UserRegistrationSerializer,
    UserLoginSerializer,
    ProfileSerializer,
    BusinessProfileSerializer,
    CustomerProfileSerializer,
)

class UserRegistrationView(APIView):
    """
    View for user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handles user registration by creating a new user.
        Returns a token and user details upon successful registration.
        """
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
    """
    View for user login.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handles user login and returns user data upon successful authentication.
        """
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_data = UserRegistrationSerializer().get_user_data(user)
            return Response(user_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve and update a user profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieves a specific profile based on the user ID in the URL.
        """
        return get_object_or_404(Profile, user_id=self.kwargs['pk'])


    def patch(self, request, *args, **kwargs):
        """
        Allows updating a profile, but only if the requesting user owns the profile.
        """
        profile = self.get_object()
        if request.user != profile.user:
            return Response({"detail": "You do not have permission to update this profile."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().patch(request, *args, **kwargs)

class BaseProfileListView(generics.ListAPIView):
    """
    Base view for listing profiles, should be subclassed for specific user types.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def get_queryset(self):
        """
        Filters profiles based on the user type, which must be defined in subclasses.
        """
        if self.user_type is None:
            raise NotImplementedError("user_type must be set in subclasses.")
        return Profile.objects.filter(user__type=self.user_type)

    def list(self, request, *args, **kwargs):
        """
        Lists profiles and returns an empty list if no profiles are found.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)
        return Response(serializer.data)

class BusinessProfileListView(BaseProfileListView):
    """
    View to list business profiles.
    """
    serializer_class = BusinessProfileSerializer
    user_type = 'business'

class CustomerProfileListView(BaseProfileListView):
    """
    View to list customer profiles.
    """
    serializer_class = CustomerProfileSerializer
    user_type = 'customer'