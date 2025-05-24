from django.conf import settings
from django.db import models
from django.utils.text import slugify

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    short_description = models.TextField(blank=True)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_new = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    # Add any more fields you need

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
    ]
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tran_id     = models.CharField(max_length=255, blank=True, null=True)  # transaction id
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    total       = models.DecimalField(max_digits=12, decimal_places=2)
    created_at  = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    bkash_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.user}"


class OrderItem(models.Model):
    order           = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product         = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity        = models.PositiveIntegerField(default=1)
    price_at_order  = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self):
        return self.quantity * self.price_at_order

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


class Payment(models.Model):
    order        = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    txn_id       = models.CharField(max_length=64, unique=True)
    amount       = models.DecimalField(max_digits=12, decimal_places=2)
    status       = models.CharField(max_length=20)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.txn_id} ({self.status})"
