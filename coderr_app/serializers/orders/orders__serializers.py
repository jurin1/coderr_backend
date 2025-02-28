from rest_framework import serializers
from django.shortcuts import get_object_or_404
from ...models import Order, OfferDetail, CustomUser

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for orders.
    Handles creation, update, and retrieval of orders placed by customers based on offer details.
    """
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
        """
        Creates a new order.
        Creates an order based on a selected offer detail, associating it with the customer and business users.
        """
        offer_detail_id = validated_data.pop('offer_detail_id')
        offer_detail = get_object_or_404(OfferDetail, id=offer_detail_id)
        offer = offer_detail.offer

        if self.context['request'].user.type != 'customer':
            raise serializers.ValidationError("Only customers can create orders.")

        order = Order.objects.create(
            customer_user=self.context['request'].user,
            business_user=offer.user,
            offer_detail=offer_detail,
            title=offer.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,
            status='in_progress',
        )
        return order

    def update(self, instance, validated_data):
        """
        Updates an existing order.
        Allows business users to update the status of an order.
        """
        if self.context['request'].user.type == 'business':
            if 'status' in validated_data:
                instance.status = validated_data['status']
                instance.save()
                return instance
        else:
            raise serializers.ValidationError("Only business users can update the order status")


class OrderCountSerializer(serializers.Serializer):
    """
    Serializer for order count.
    Used to return the count of orders.
    """
    order_count = serializers.IntegerField()

class CompletedOrderCountSerializer(serializers.Serializer):
    """
    Serializer for completed order count.
    Used to return the count of completed orders.
    """
    completed_order_count = serializers.IntegerField()