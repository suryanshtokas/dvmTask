from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import ListView, FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Wallet, Transaction
from .forms import TopUpForm
from carpool.models import CarpoolOffer


class WalletView(LoginRequiredMixin, TemplateView):
    template_name = "payments/wallet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wallet"] = self.request.user.wallet
        context["transactions"] = Transaction.objects.filter(
            user = self.request.user,
        ).order_by("-created_at")

        return context
    

class TopUpView(LoginRequiredMixin, FormView):
    template_name = "payments/topup.html"
    form_class = TopUpForm
    success_url = reverse_lazy("wallet")

    def form_valid(self, form):
        amount = form.cleaned_data["amount"]
        wallet = self.request.user.wallet
        wallet.balance += amount
        wallet.save()

        Transaction.objects.create(
            user = self.request.user,
            transaction_type = "topup",
            amount = amount,
            description = f"Wallet top-up of ${amount}",
        )

        messages.success(self.request, f"Successfully topped up ${amount}")
        return super().form_valid(form)


class DriverEarningsView(LoginRequiredMixin, ListView):
    template_name = "payments/driver_earnings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        earnings = Transaction.objects.filter(
            user = self.request.user,
            transaction_type = "earning",
        ).order_by("-created_at")

        context["earnings"] = earnings
        context["total_earnings"] = sum(e.amount for e in earnings)
        context["wallet"] = self.request.user.wallet
        return context
