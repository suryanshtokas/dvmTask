from django.contrib import admin

from .models import Wallet, Transaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "updated_at"]
    search_fields = ["user__username"]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "transaction_type", "amount", "trip", "created_at"]
    list_filter = ["transaction_type"]
    search_fields = ["user__username"]

