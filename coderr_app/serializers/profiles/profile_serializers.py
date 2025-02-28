from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from ...models import Profile

User = get_user_model()

class BaseProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the base profile information.
    It includes fields common to both customer and business profiles.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    type = serializers.CharField(source='user.type', read_only=True)
    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'type']
        read_only_fields = ('user',)

class CustomerProfileSerializer(BaseProfileSerializer):
    """
    Serializer for customer profiles.
    Inherits from BaseProfileSerializer and uses the same fields.
    """
    class Meta(BaseProfileSerializer.Meta):
        fields = BaseProfileSerializer.Meta.fields
class BusinessProfileSerializer(BaseProfileSerializer):
    """
    Serializer for business profiles.
    Inherits from BaseProfileSerializer and adds business-specific fields.
    """
    class Meta(BaseProfileSerializer.Meta):
        fields = BaseProfileSerializer.Meta.fields + ['location', 'tel', 'description', 'working_hours']

class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for general profile information, used for updating profiles.
    Includes fields for both customer and business profiles and allows updates to user details.
    """
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    type = serializers.CharField(source='user.type', required=False)

    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel',
                  'description', 'working_hours', 'type', 'email', 'created_at']
        read_only_fields = ('user', 'created_at')

    def update(self, instance, validated_data):
        """
        Updates the profile instance.
        Handles updates to both Profile fields and related User fields.
        """
        user_data = validated_data.pop('user', {})
        instance = super().update(instance, validated_data)

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                if hasattr(user, attr):
                    setattr(user, attr, value)
            user.save()

        return instance

class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Handles validation and creation of new users, including password validation and token generation.
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=[('customer', 'Customer'), ('business', 'Business')])
    user_id = serializers.IntegerField(read_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        """
        Validates registration data.
        Checks if passwords match and validates password complexity.
        """
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        """
        Creates a new user.
        Creates a new user instance, sets the user type, and generates an authentication token.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.type = validated_data['type']
        user.save()

        token, created = Token.objects.get_or_create(user=user)
        validated_data['token'] = token.key
        validated_data['user_id'] = user.id

        return validated_data

    def get_user_data(self, user):
        """
        Returns user data including token.
        Helper function to retrieve user data and token.
        """
        token, created = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
        }

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Handles username and password authentication.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validates login credentials.
        Authenticates the user using provided username and password.
        """
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

        data['user'] = user
        return data