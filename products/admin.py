from django.contrib import admin
from .models import Product, Label

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'stock')
    search_fields = ('name', 'sku')
    list_filter = ('labels',)

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
