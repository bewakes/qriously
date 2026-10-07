import pytest

from accounts.models import DeviceSession
from accounts.policies import hash_token
from accounts.services import create_anonymous_session


@pytest.mark.django_db
def test_create_anonymous_session():
    user, session, raw_token = create_anonymous_session(label="pytest")

    assert user.is_anonymous_device is True
    assert user.email is None
    assert user.has_usable_password() is False
    assert session.user_id == user.id
    assert session.label == "pytest"
    assert session.is_active is True
    assert session.token_hash == hash_token(raw_token)


@pytest.mark.django_db
def test_revoke():
    _user, session, raw_token = create_anonymous_session()
    assert DeviceSession.objects.filter(token_hash=hash_token(raw_token)).exists()

    session.revoke()

    session.refresh_from_db()
    assert session.is_active is False
