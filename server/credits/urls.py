from django.urls import path

from .api import LedgerView, WalletBalanceView

urlpatterns = [
    path("credits/balance", WalletBalanceView.as_view(), name="credits-balance"),
    path("credits/ledger", LedgerView.as_view(), name="credits-ledger"),
]
