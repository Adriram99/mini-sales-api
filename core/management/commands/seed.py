from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from faker import Faker
import random
from products.models import Label, Product
from customers.models import Customer
from orders.models import Order, OrderItem

fake = Faker()

class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **kwargs):
        # clear existing data
        self.stdout.write('Clearing existing data...')
        Product.objects.all().delete()
        Label.objects.all().delete()
        Customer.objects.all().delete()
        Order.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        # users data test
        users_data = [
            {'username': 'manager1', 'password': 'managerpass', 'group': 'Manager'},
            {'username': 'seller1', 'password': 'sellerpass', 'group': 'Seller'},
            {'username': 'viewer1', 'password': 'viewerpass', 'group': 'Viewer'},
            {'username': 'norole', 'password': 'norolepass', 'group': False}
        ]

        self.stdout.write('Seeding data...')
        self.seed_users(users_data)
        self.seed_labels(10)
        self.seed_products(10)
        self.seed_customers(10)
        self.seed_orders(10)
        self.stdout.write('Seeding completed.')
    
    def seed_users(self, users_data):
        # obtain groups
        groups = {g.name: g for g in Group.objects.all()}

        for user_data in users_data:
            user, created = User.objects.get_or_create(username=user_data['username'])
            user.set_password(user_data['password'])
            user.save()
            if user_data["group"] in groups:
                user.groups.set([groups[user_data["group"]]])
                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" created and added to group "{user_data["group"]}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.username}" without assigned group. It created anyway.'))

    def seed_labels(self, count):
        for _ in range(count):
            Label.objects.create(name=fake.unique.word())
        self.stdout.write(f'Created {count} labels.')

    def seed_products(self, count):
        labels = list(Label.objects.all())
        for _ in range(count):
            product = Product.objects.create(
                name=fake.word().capitalize(),
                sku= fake.unique.bothify(text='SKU-########'),
                price = fake.random_number(digits=5),
                stock = random.randint(10, 100)
            )
            product.labels.set(random.sample(labels, k=random.randint(1, len(labels))))
        self.stdout.write(f'Created {count} products.')

    def seed_customers(self, count):
        for _ in range(count):
            Customer.objects.create(
                full_name=fake.name(),
                email=fake.unique.email()
            )
        self.stdout.write(f'Created {count} customers.')

    def seed_orders(self, count):
        customers = list(Customer.objects.all())
        products = list(Product.objects.all())
        for _ in range(count):
            customer = random.choice(customers)
            order = Order.objects.create(customer=customer)
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                OrderItem.objects.create(order=order, 
                                         product=product, 
                                         quantity=quantity,
                                         unit_price=product.price)
        self.stdout.write(f'Created {count} orders.')
