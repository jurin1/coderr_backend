from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from ...models import Order, CustomUser
from ...serializers.orders.orders__serializers import OrderSerializer, OrderCountSerializer, CompletedOrderCountSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    View to list and create orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves orders related to the current user, either as a customer or business user.
        """
        user = self.request.user
        return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))

    def create(self, request, *args, **kwargs):
        """
        Creates a new order.
        """
        return super().create(request, *args, **kwargs)

class OrderUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, and delete orders.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retrieves a specific order, handling DoesNotExist exceptions.
        """
        try:
            order = super().get_object()
        except Order.DoesNotExist:
            return Response({"detail": "The specified order was not found."}, status=status.HTTP_404_NOT_FOUND)
        return order


    def update(self, request, *args, **kwargs):
        """
        Updates an order's status, only allowed for the assigned business user.
        Validates status values and handles missing status field.
        """
        order = self.get_object()
        if isinstance(order, Response):
            return order

        if request.user.type != "business" or request.user.id != order.business_user.id:
            return Response({"detail": "Only the assigned business user can update the status of this order."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            if 'status' in request.data:
                valid_status_values = ['in_progress', 'completed', 'cancelled']
                if request.data['status'] not in valid_status_values:
                    return Response({"detail": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                 return Response({"detail": "The 'status' field is missing in the request body."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):
        """
        Deletes an order, only allowed for admin users.
        """
        instance = self.get_object()
        if isinstance(instance, Response):
            return instance
        if not request.user.is_staff:
            return Response({"detail": "Only admin users are allowed to delete orders."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """
        Deletes the order instance.
        """
        instance.delete()

    def handle_exception(self, exc):
        """
        Handles exceptions, specifically Order.DoesNotExist.
        """
        if isinstance(exc, Order.DoesNotExist):
            return Response({"detail": "The specified order was not found."}, status=status.HTTP_404_NOT_FOUND)
        return super().handle_exception(exc)


class OrderCountView(generics.RetrieveAPIView):
    """
    View to retrieve the count of in-progress orders for a business user.
    """
    serializer_class = OrderCountSerializer
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        """
        Retrieves and returns the count of in-progress orders for a given business user ID.
        """
        business_user_id = self.kwargs['business_user_id']
        get_object_or_404(CustomUser, id=business_user_id, type='business')

        order_count = Order.objects.filter(business_user_id=business_user_id, status='in_progress').count()
        serializer = self.get_serializer({'order_count': order_count})
        return Response(serializer.data)


class CompletedOrderCountView(generics.RetrieveAPIView):
    """
    View to retrieve the count of completed orders for a business user.
    """
    serializer_class = CompletedOrderCountSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Retrieves and returns the count of completed orders for a given business user ID.
        """
        business_user_id = self.kwargs['business_user_id']
        get_object_or_404(CustomUser, id=business_user_id, type='business')

        completed_order_count = Order.objects.filter(business_user_id=business_user_id, status='completed').count()
        serializer = self.get_serializer({'completed_order_count': completed_order_count})
        return Response(serializer.data)