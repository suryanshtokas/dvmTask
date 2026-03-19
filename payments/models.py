from django.db import models
from django.contrib.auth.models import User 
from trips.models import Trip

from django.db.models.signals import post_save
from django.dispatch import receiver


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet - Balance: ${self.balance}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("topup", "Top Up"),
        ("deduction", "Deduction"),
        ("earning", "Earning"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ${self.amount} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    

# ensuring a wallet is created every time a new user is created
@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
