from django.db import models

# Create your models here.
class Label(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.IntegerField()
    labels = models.ManyToManyField(Label, related_name='products')

    def __str__(self):
        return f"{self.name} ({self.sku})"
