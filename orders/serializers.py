from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from django.db import transaction

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']
    
    def get_subtotal(self, obj):
        return obj.subtotal()

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'created_at', 'items', 'total_amount']
    
    def get_total_amount(self, obj):
        return obj.total()

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        # guaranteed atomic transaction
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
        
            # recolect product IDs or instances
            product_ids = []
            for it in items_data:
                prod = it['product']
                pid = int(prod) if isinstance(prod, (int, str)) else prod.pk
                product_ids.append(pid)

            # lock products in one query
            products_map = {
                p.id: p
                for p in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']

                pid = int(prod) if isinstance(prod, (int, str)) else prod.pk

                product = products_map.get(pid)
                if product is None:
                    raise serializers.ValidationError(f"Product {pid} not found")

                # validate stock availability
                if product.stock < quantity:
                    raise serializers.ValidationError(f"Insufficient stock for product {product.name}")

                # freeze the unit price at the time of order creation
                unit_price = product.price
            
                # reduce stock
                product.stock -= quantity
                product.save(update_fields=['stock'])

                OrderItem.objects.create(order=order, 
                                        product=product, 
                                        quantity=quantity, 
                                        unit_price=unit_price)

        return order