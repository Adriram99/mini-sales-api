from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order
from .serializers import OrderSerializer
from .filters import OrderFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction


# Create your views here.
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("customer").prefetch_related("items__product")
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    # POST /orders/{id}/pay/ -> to pay for an order
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        if order.status == 'PAID':
            return Response({'error': 'Order already paid'}, status=status.HTTP_400_BAD_REQUEST)
        if order.status != 'PENDING':
            return Response({'error': 'Order cannot be paid'}, status=status.HTTP_409_CONFLICT)
        
        with transaction.atomic():
            order.status = 'PAID'
            order.save(update_fields=['status'])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
    
    # POST /orders/{id}/cancel/ -> to cancel an order
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status == 'CANCELLED':
            return Response({'error': 'Order already cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        if order.status not in ['PENDING']:
            return Response({'error': 'Order cannot be canceled'}, status=status.http_409_CONFLICT)
        
        with transaction.atomic():
            items = order.items.select_related('product').select_for_update()
            # restock items
            for item in items:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])
            
        order.status = 'CANCELLED'
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)