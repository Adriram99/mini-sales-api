# from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter

from .models import Product, Label
from .serializers import ProductSerializer, ProductCreateUpdateSerializer, LabelSerializer
from .filters import ProductFilter



# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProductFilter
    ordering = ['id']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def perform_update(self, serializer):
        try:
            return super().perform_update(serializer)
        except IntegrityError as e:
            raise ValidationError({"detail": str(e)})

    # POST /products/{id}/labels/ -> add label to product
    @action(detail=True, methods=['post'])
    def labels(self, request, pk=None):
        product = self.get_object()
        label_id = request.data.get('label_id')
        label_name = request.data.get('label_name')
        
        if label_id:
            try:
                label = Label.objects.get(id=label_id)
            except Label.DoesNotExist:
                return Response({'error': 'Label not found'}, status=status.HTTP_404_NOT_FOUND)
        elif label_name:
            label, _ = Label.objects.get_or_create(name=label_name)
        else:
            return Response({'error': 'Provide label_id or label_name'}, status=status.HTTP_400_BAD_REQUEST)
        
        product.labels.add(label)
        return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_200_OK)

    # DELETE /products/{id}/remove_label/ -> remove label from product
    @action(detail=True, methods=["delete"], url_path="labels/(?P<label_id>[^/.]+)")
    def remove_label(self, request, pk=None, label_id=None):
        product = self.get_object()
        try:
            label = Label.objects.get(id=label_id)
        except Label.DoesNotExist:
            return Response({"error": "Label not found"}, status=status.HTTP_404_NOT_FOUND)

        product.labels.remove(label)
        return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
    
class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
