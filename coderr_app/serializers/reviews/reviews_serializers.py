from rest_framework import serializers
from ...models import Review, CustomUser

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviews.
    Handles creation, update, and retrieval of reviews submitted by customers for business users.
    """
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    business_user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.filter(type='business'))
    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ('created_at', 'updated_at', 'reviewer')

    def validate(self, data):
        """
        Validates review data.
        Ensures only customers can create reviews and prevents duplicate reviews for the same business by the same customer.
        """
        if self.context['request'].user.type != 'customer':
            raise serializers.ValidationError("Only customers can create reviews.")

        if self.instance is None:
            business_user = data['business_user']
            reviewer = self.context['request'].user
            if Review.objects.filter(business_user=business_user, reviewer=reviewer).exists():
                raise serializers.ValidationError("You have already submitted a review for this business.")
        return data

    def update(self, instance, validated_data):
        """
        Updates an existing review.
        Allows updating the rating and description of a review.
        """
        instance.rating = validated_data.get('rating', instance.rating)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance