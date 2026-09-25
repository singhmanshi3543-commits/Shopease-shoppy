from django.contrib import admin
from .models import Product, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

  list_display = (
'name',
'category',
'price',
'stock',
'created_at',
)

list_filter = (
    'category',
    'created_at',
)

search_fields = (
    'name',
    'description',
)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
  list_display = (
'id',
'user',
'full_name',
'total_amount',
'status',
'created_at',
)

list_filter = (
    'status',
    'created_at',
)

search_fields = (
    'full_name',
    'email',
    'phone',
    'user__username',
)

ordering = (
    '-created_at',
)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    
  list_display = (
'order',
'product',
'quantity',
'price',
'subtotal',
)

search_fields = (
    'product__name',
    'order__id',
)