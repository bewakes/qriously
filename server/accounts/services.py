from __future__ import annotations

from django.db import transaction

from core import constants

from .models import Session, User
from .policies import generate_token
from .providers import (
    AuthError,
    AuthProvider,
    DevCodeProvider,
    GoogleProvider,
    Identity,
    InMemoryCodeStore,
)

_code_store = InMemoryCodeStore(
    ttl_seconds=constants.LOGIN_CODE_TTL_SECONDS,
    length=constants.LOGIN_CODE_LENGTH,
)

_providers: dict[str, AuthProvider] = {
    "dev": DevCodeProvider(_code_store),
    "google": GoogleProvider(),
}


def get_auth_provider(name: str | None = None) -> AuthProvider:
    provider = _providers.get(name or constants.AUTH_PROVIDER)
    if provider is None:
        raise AuthError("unknown_provider")
    return provider


@transaction.atomic
def create_anonymous_session(
    label: str = "",
) -> tuple[User, Session, str]:
    user = User.objects.create_user(is_anonymous_device=True)
    raw_token, token_hash = generate_token()
    session = Session.objects.create(
        user=user, token_hash=token_hash, label=label
    )
    return user, session, raw_token


def _issue_session(user: User, label: str = "") -> tuple[Session, str]:
    raw_token, token_hash = generate_token()
    session = Session.objects.create(
        user=user, token_hash=token_hash, label=label
    )
    return session, raw_token


@transaction.atomic
def claim_anonymous_user(
    user: User, email: str, display_name: str = ""
) -> User:
    """Bind an email to an existing anonymous session, in place.

    No rows move: threads, notes and the wallet stay attached because the
    primary key is unchanged, so the whole local history is preserved.
    """
    if not user.is_anonymous_device:
        raise AuthError("already_claimed")
    user.email = email
    if display_name and not user.display_name:
        user.display_name = display_name
    user.is_anonymous_device = False
    user.save(
        update_fields=[
            "email",
            "display_name",
            "is_anonymous_device",
            "updated_at",
        ]
    )
    return user


@transaction.atomic
def login(
    identity: Identity,
    *,
    current_session: Session | None = None,
    label: str = "",
) -> tuple[User, Session, str]:
    """Resolve a verified identity to an account and issue a fresh session.

    An anonymous session that logs in for an unregistered email is claimed in
    place; a registered email issues a new session for that account (no merge).
    """
    email = identity.email.strip().lower()
    user = User.objects.filter(email__iexact=email).first()

    if (
        user is None
        and current_session is not None
        and current_session.user.is_anonymous_device
    ):
        user = claim_anonymous_user(
            current_session.user, email, display_name=identity.display_name
        )

    if user is None:
        user = User.objects.create_user(
            email=email,
            display_name=identity.display_name,
            is_anonymous_device=False,
        )

    session, raw_token = _issue_session(user, label=label)
    if current_session is not None and current_session.user_id == user.id:
        current_session.revoke()
    return user, session, raw_token
