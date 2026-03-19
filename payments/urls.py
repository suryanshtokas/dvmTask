from django.urls import path
from .views import WalletView, TopUpView, DriverEarningsView

urlpatterns = [
    path("wallet/", WalletView.as_view(), name="wallet"),
    path("wallet/topup/", TopUpView.as_view(), name="topup"),
    path("earnings/", DriverEarningsView.as_view(), name="driver_earnings"),
]