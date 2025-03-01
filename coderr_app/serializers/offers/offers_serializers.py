from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from ...models import Offer, OfferDetail, Profile

class OfferDetailBriefSerializer(serializers.ModelSerializer):
    """
    A concise serializer for OfferDetail, only showing id and url.
    """
    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail', read_only=True)

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for offer details.  (Full details, used for creation/updates)
    Represents specific details within an offer, like price, revisions, delivery time.
    """
    id = serializers.IntegerField(required=False)
    url = serializers.HyperlinkedIdentityField(view_name='offerdetail-detail', read_only=True)
    offer = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = OfferDetail
        fields = '__all__'

    def validate_delivery_time_in_days(self, value):
        """
        Validates delivery time.
        Ensures delivery time is a positive integer.
        """
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("Delivery time (in days) must be a positive integer.")
        return value

    def to_representation(self, instance):
        """
        Customizes the serialization to return price as an integer (int).
        """
        representation = super().to_representation(instance)
        if representation.get('price') is not None:
            representation['price'] = int(float(representation['price']))
        return representation


class OfferSerializer(serializers.ModelSerializer):
    """
    Serializer for offers.
    Handles creation, update, and retrieval of offers, including nested offer details.
    """
    details = OfferDetailBriefSerializer(many=True, read_only=True)  # Use the concise serializer, and make it read_only
    details_data = OfferDetailSerializer(many=True, write_only=True, source='details') # For write operations, but don't include in output
    user_details = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 'updated_at', 'details', 'details_data', 'min_price', 'min_delivery_time', 'user_details']
        read_only_fields = ('created_at', 'updated_at', 'user')

    def get_user_details(self, obj):
        """
        Retrieves user details for the offer.
        Returns first name, last name, and username of the user who created the offer.
        """
        profile = Profile.objects.get(user=obj.user)
        return {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "username": profile.user.username,
        }

    def create(self, validated_data):
        """
        Creates a new offer.
        Handles creation of an offer and its associated offer details.
        """
        details_data = validated_data.pop('details')  # Use the correct source
        offer = Offer.objects.create(user=self.context['request'].user, **validated_data)
        for detail_data in details_data:
            if 'delivery_time_in_days' not in detail_data or detail_data['delivery_time_in_days'] is None:
                raise serializers.ValidationError("Delivery time (in days) is required for each offer detail.")
            if not isinstance(detail_data['delivery_time_in_days'], int) or detail_data['delivery_time_in_days'] <= 0:
                 raise serializers.ValidationError("Delivery time (in days) must be a positive integer.")

            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def validate(self, data):
        """
        Validates offer data.
        Ensures only business users can create offers and that offer details are provided and unique.
        """
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
        """
        Updates an existing offer.
        Handles updates to the offer and its associated offer details.
        """
        details_data = validated_data.pop('details', None) # Use the correct source

        instance.title = validated_data.get('title', instance.title)
        instance.image = validated_data.get('image', instance.image)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        if details_data is not None:
            self.update_details(instance, details_data)

        return instance

    def update_details(self, offer, details_data):
        """
        Updates offer details for an offer.
        Handles updating, creating, and deleting offer details associated with an offer.
        """
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

    def to_representation(self, instance):
        """
        Customizes the serialization to return min_price as a number (float).
        """
        representation = super().to_representation(instance)
        if representation.get('min_price') is not None:
            representation['min_price'] = int(float(representation['min_price']))
        return representation