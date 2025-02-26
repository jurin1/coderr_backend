from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from .models import Profile, FileUpload, Offer, OfferDetail, Order, CustomUser, Review
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

class OfferDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  
    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail', read_only=True)
    offer = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = OfferDetail
        fields = '__all__'

    def validate_delivery_time_in_days(self, value): 
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("Delivery time (in days) must be a positive integer.")
        return value

class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
    user_details = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        read_only_fields = ('created_at', 'updated_at', 'user')

    def get_user_details(self, obj):
        profile = Profile.objects.get(user=obj.user)
        return {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "username": profile.user.username,
        }

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(user=self.context['request'].user, **validated_data)
        for detail_data in details_data:
            
            if 'delivery_time_in_days' not in detail_data or detail_data['delivery_time_in_days'] is None:
                raise serializers.ValidationError("Delivery time (in days) is required for each offer detail.")
            if not isinstance(detail_data['delivery_time_in_days'], int) or detail_data['delivery_time_in_days'] <= 0:
                 raise serializers.ValidationError("Delivery time (in days) must be a positive integer.")

            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.type != 'business':
            raise serializers.ValidationError("Only business users can create offers.")

        details_data = data.get('details')
        if not details_data:
            raise serializers.ValidationError("At least one offer detail is required.")
       
        offer_types = [detail.get('offer_type') for detail in details_data if detail.get('offer_type')]
        if len(offer_types) != len(set(offer_types)):
            raise serializers.ValidationError("Duplicate offer types are not allowed.")

        return data
    
    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)  

        instance.title = validated_data.get('title', instance.title)
        instance.image = validated_data.get('image', instance.image)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        if details_data is not None:
            self.update_details(instance, details_data)

        return instance

    def update_details(self, offer, details_data):
        existing_details = {detail.id: detail for detail in offer.details.all()}
        updated_detail_ids = []

        with transaction.atomic():
            for detail_data in details_data:
                detail_id = detail_data.get('id')

                if detail_id:
                    detail = existing_details.get(detail_id)
                    if detail:
                        serializer = OfferDetailSerializer(detail, data=detail_data, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        updated_detail_ids.append(detail_id)

                else:
                    serializer = OfferDetailSerializer(data=detail_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(offer=offer)

            for detail_id, detail in existing_details.items():
                if detail_id not in updated_detail_ids:
                    detail.delete()
    
class OrderSerializer(serializers.ModelSerializer):
    customer_user = serializers.PrimaryKeyRelatedField(read_only=True)
    business_user = serializers.PrimaryKeyRelatedField(read_only=True)
    offer_detail_id = serializers.IntegerField(write_only=True)  

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'offer_detail_id', 
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = (
            'customer_user',
            'business_user',
            'created_at',
            'updated_at',
            'title',  
            'revisions',  
            'delivery_time_in_days',  
            'price',  
            'features',  
            'offer_type'
        )

    def create(self, validated_data):
        offer_detail_id = validated_data.pop('offer_detail_id')
        offer_detail = get_object_or_404(OfferDetail, id=offer_detail_id)
        offer = offer_detail.offer

        if self.context['request'].user.type != 'customer':
            raise serializers.ValidationError("Only customers can create orders.")

        order = Order.objects.create(
            customer_user=self.context['request'].user,
            business_user=offer.user,
            offer_detail=offer_detail,
            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress',  
        )
        return order

    def update(self, instance, validated_data):
        if self.context['request'].user.type == 'business':
            if 'status' in validated_data:
                instance.status = validated_data['status']
                instance.save()
                return instance
        else:
            raise serializers.ValidationError("Only business users can update the order status")


class OrderCountSerializer(serializers.Serializer):
    order_count = serializers.IntegerField()

class CompletedOrderCountSerializer(serializers.Serializer):
    completed_order_count = serializers.IntegerField()

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    business_user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.filter(type='business'))
    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at', 'reviewer')

    def validate(self, data):
        if self.context['request'].user.type != 'customer':
            raise serializers.ValidationError("Only customers can create reviews.")

        if self.instance is None:  
            business_user = data['business_user']
            reviewer = self.context['request'].user
            if Review.objects.filter(business_user=business_user, reviewer=reviewer).exists():
                raise serializers.ValidationError("You have already submitted a review for this business.")
        return data
    
    def update(self, instance, validated_data):
        instance.rating = validated_data.get('rating', instance.rating)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    

