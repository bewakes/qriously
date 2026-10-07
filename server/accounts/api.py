from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.api import WalletSerializer
from credits.services import get_wallet

from .models import User
from .services import create_anonymous_session


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "is_anonymous_device", "created_at"]
        read_only_fields = fields


class DeviceAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        label = (request.data.get("label") or "")[:200]
        user, _session, token = create_anonymous_session(label=label)
        wallet = get_wallet(user)
        return Response(
            {
                "token": token,
                "user": UserSerializer(user).data,
                "wallet": WalletSerializer(wallet).data,
                "granted": wallet.lifetime_granted,
            },
            status=201,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = get_wallet(request.user)
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "wallet": WalletSerializer(wallet).data,
            }
        )
