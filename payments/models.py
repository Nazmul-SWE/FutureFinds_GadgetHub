from django.db import models
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('paid','Paid'),
        ('failed','Failed'),
        ('cancelled','Cancelled'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='BDT')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Order #{self.id} ({self.status}) - {self.amount} {self.currency}"

class Transaction(models.Model):
    order = models.ForeignKey(Order, related_name='transactions', on_delete=models.CASCADE)
    gateway = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    raw_response = models.JSONField(null=True, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gateway} tx {self.transaction_id} ({'ok' if self.success else 'pending'})"

