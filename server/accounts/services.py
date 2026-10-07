from django.db import transaction

from .models import DeviceSession, User
from .policies import generate_token


@transaction.atomic
def create_anonymous_session(label=""):
    user = User.objects.create_user(is_anonymous_device=True)
    raw_token, token_hash = generate_token()
    session = DeviceSession.objects.create(
        user=user, token_hash=token_hash, label=label
    )
    return user, session, raw_token
