from rest_framework import serializers
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CreditEntry, Wallet
from .services import get_wallet


class WalletSerializer(serializers.ModelSerializer):
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["balance", "lifetime_granted", "lifetime_spent", "currency"]

    def get_currency(self, _obj: Wallet) -> str:
        return "micro_credits"


class CreditEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditEntry
        fields = [
            "id",
            "delta",
            "balance_after",
            "entry_type",
            "reason",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class WalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(WalletSerializer(get_wallet(request.user)).data)


class LedgerPagination(CursorPagination):
    page_size = 50
    ordering = "-created_at"


class LedgerView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LedgerPagination

    def get(self, request: Request) -> Response:
        queryset = CreditEntry.objects.filter(wallet=get_wallet(request.user))
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = CreditEntrySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
