import csv
from celery import shared_task
from django.utils import timezone
from .models import Order

# @shared_task
# def hello_celery():
#     print("Hello, Celery!")

@shared_task
def export_daily_orders_to_csv():
    """
    Task to export all orders to a CSV file.
    """
    now = timezone.now()
    since = now - timezone.timedelta(hours=24)
    
    orders = Order.objects.filter(created_at__gte=since, created_at__lte=now)

    if not orders.exists():
        return f"No orders found in the last 24 hours."
    
    filename = f"/tmp/daily_sales_{now.strftime('%Y%m%d')}.csv"

    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Order ID', 'Customer Email', 'Items Count', 'Total Amount', 'Status', 'Created At'])

        for order in orders:
            items_count = order.items.count()
            writer.writerow([
                order.id,
                order.customer.email,
                items_count,
                order.total(),
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

    return f"CSV generated: {filename}"
        

    