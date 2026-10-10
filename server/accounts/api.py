from __future__ import annotations

import logging

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.api import WalletSerializer
from credits.services import get_wallet

from .authentication import SessionTokenAuthentication
from .models import Session, User
from .providers import AuthError
from .services import create_anonymous_session, get_auth_provider, login

logger = logging.getLogger("accounts.auth")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "is_anonymous_device", "created_at"]
        read_only_fields = fields


class DeviceAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
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


def _current_session(request: Request) -> Session | None:
    try:
        result = SessionTokenAuthentication().authenticate(request)
    except AuthenticationFailed:
        return None
    return result[1] if result else None


class LoginStartView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        email = (request.data.get("email") or "").strip()
        provider = get_auth_provider()
        try:
            code = provider.start(email)
        except AuthError as exc:
            return Response({"error": str(exc)}, status=400)
        if code is not None:
            logger.warning("Qriously login code for %s: %s", email, code)
        return Response(
            {
                "sent": True,
                "provider": provider.name,
                "requires_code": provider.requires_code,
            }
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        email = (request.data.get("email") or "").strip()
        credential = (
            request.data.get("code") or request.data.get("credential") or ""
        ).strip()
        try:
            provider = get_auth_provider(request.data.get("provider"))
        except AuthError as exc:
            return Response({"error": str(exc)}, status=400)
        try:
            identity = provider.verify(email, credential)
        except AuthError as exc:
            return Response({"error": str(exc)}, status=401)

        label = (request.data.get("label") or "")[:200]
        user, _session, token = login(
            identity, current_session=_current_session(request), label=label
        )
        wallet = get_wallet(user)
        return Response(
            {
                "token": token,
                "user": UserSerializer(user).data,
                "wallet": WalletSerializer(wallet).data,
                "granted": wallet.lifetime_granted,
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        wallet = get_wallet(request.user)
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "wallet": WalletSerializer(wallet).data,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        session = request.auth
        if isinstance(session, Session):
            session.revoke()
        return Response(status=204)

