import django_filters
from .models import Order

class OrderFilter(django_filters.FilterSet):
    customer_email = django_filters.CharFilter(field_name='customer__email', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Order
        fields = ['customer_email', 'status', 'date_from', 'date_to']
