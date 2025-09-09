from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q


# Create your models here.
class Label(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    labels = models.ManyToManyField(Label, related_name='products')

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    class Meta:
        constrains = [
            models.CheckConstraint(check=Q(stock__gte=0), name='stock_gte_0'),
        ]
