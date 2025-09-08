from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order
from .serializers import OrderSerializer

# Create your views here.
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("customer").prefetch_related("items__product")
    serializer_class = OrderSerializer

    # POST /orders/{id}/pay/ -> to pay for an order
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        if order.status != 'PENDING':
            return Response({'error': 'Order cannot be paid'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'paid'
        order.save()
        return Response(OrderSerializer(order).data)
    
    # POST /orders/{id}/cancel/ -> to cancel an order
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in ['PENDING', 'PAID']:
            return Response({'error': 'Order cannot be canceled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # restock items
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
            
        order.status = 'canceled'
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)