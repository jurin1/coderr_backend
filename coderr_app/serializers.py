from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from .models import Profile, FileUpload
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    type = serializers.CharField(source='user.type', read_only=True)
    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'type']
        read_only_fields = ('user',) 

class CustomerProfileSerializer(BaseProfileSerializer):
    class Meta(BaseProfileSerializer.Meta):  
        
        fields = BaseProfileSerializer.Meta.fields 
class BusinessProfileSerializer(BaseProfileSerializer):
    class Meta(BaseProfileSerializer.Meta): 
        fields = BaseProfileSerializer.Meta.fields + ['location', 'tel', 'description', 'working_hours']

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    type = serializers.CharField(source='user.type', required=False) 

    class Meta:
        model = Profile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel',
                  'description', 'working_hours', 'type', 'email', 'created_at']
        read_only_fields = ('user', 'created_at')

    def update(self, instance, validated_data):
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
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=[('customer', 'Customer'), ('business', 'Business')])
    user_id = serializers.IntegerField(read_only=True)
    token = serializers.CharField(read_only=True) 

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['password']) 
        return data

    def create(self, validated_data):
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
        token, created = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id,
        }
    
class UserLoginSerializer(serializers.Serializer): 
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
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
    

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['file', 'uploaded_at']