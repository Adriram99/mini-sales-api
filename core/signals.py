from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

def create_roles(sender, **kwargs):
    # reassure that the apps are migrated
    # if sender.name not in ['products', 'customers', 'orders']:
    #     return
    
    # obtain content types for the models in the app
    product_ct = ContentType.objects.get_for_model(apps.get_model('products', 'Product'))
    labels_ct = ContentType.objects.get_for_model(apps.get_model('products', 'Label'))
    customer_ct = ContentType.objects.get_for_model(apps.get_model('customers', 'Customer'))
    order_ct = ContentType.objects.get_for_model(apps.get_model('orders', 'Order'))

    # create manager group with all permissions
    manager_group, _ = Group.objects.get_or_create(name='Manager')
    manager_group.permissions.set(Permission.objects.all())

    # create seller group with specific permissions
    seller_group, _ = Group.objects.get_or_create(name='Seller')
    seller_perms = Permission.objects.filter(
        content_type__in=[product_ct, labels_ct, order_ct, customer_ct],
        codename__in=[
            'view_product',
            'view_label',
            'add_customer', 'change_customer', 'view_customer',
            'add_order', 'change_order', 'view_order'
        ]
    )
    seller_group.permissions.set(seller_perms)

    # create viewer group with view permissions only
    viewer_group, _ = Group.objects.get_or_create(name='Viewer')
    viewer_perms = Permission.objects.filter(
        content_type__in=[product_ct, labels_ct, order_ct, customer_ct],
        codename__startswith='view_'
    )
    viewer_group.permissions.set(viewer_perms)

def setup_roles():
    post_migrate.connect(create_roles, weak=False)

@receiver(post_migrate)
def setup_export_csv_task(sender, **kwargs):
    if sender.name != 'orders':
        return

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='22',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*'
    )

    PeriodicTask.objects.get_or_create(
        crontab=schedule,
        name='Export Orders to CSV at 22 hs',
        task="orders.tasks.export_daily_orders_to_csv",
        defaults={'args': json.dumps([])}
    )
