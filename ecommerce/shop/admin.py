from django.contrib import admin
from .models import Product  # Import your Product model
from .models import Product, Order, OrderItem

admin.site.register(Product)  # Register it
admin.site.register(Order)
admin.site.register(OrderItem)
