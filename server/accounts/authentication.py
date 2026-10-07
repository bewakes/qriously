from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import DeviceSession
from .policies import hash_token


class DeviceTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword.lower().encode():
            return None
        if len(header) != 2:
            raise AuthenticationFailed("Invalid Authorization header.")
        try:
            token = header[1].decode()
        except UnicodeError:
            raise AuthenticationFailed("Invalid token.") from None

        try:
            session = DeviceSession.objects.select_related("user").get(
                token_hash=hash_token(token), revoked_at__isnull=True
            )
        except DeviceSession.DoesNotExist:
            raise AuthenticationFailed("Invalid or revoked token.") from None

        return (session.user, session)

    def authenticate_header(self, request):
        return self.keyword
