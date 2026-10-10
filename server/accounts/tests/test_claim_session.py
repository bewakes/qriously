import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import User
from accounts.services import create_anonymous_session
from learning.models import Thread


@pytest.mark.django_db
def test_claim_session_attaches_threads_to_account():
    anon_user, _session, _token = create_anonymous_session(label="pytest")
    Thread.objects.create(user=anon_user, title="A past session")
    target = User.objects.create_user(
        email="owner@example.com", is_anonymous_device=False
    )

    call_command("claim_session", email="owner@example.com", all_anonymous=True)

    assert Thread.objects.filter(user=target).count() == 1
    assert Thread.objects.filter(user=anon_user).count() == 0


@pytest.mark.django_db
def test_claim_session_requires_a_source():
    User.objects.create_user(email="owner@example.com", is_anonymous_device=False)
    with pytest.raises(CommandError):
        call_command("claim_session", email="owner@example.com")


@pytest.mark.django_db
def test_claim_session_rejects_anonymous_target():
    anon_user, _session, _token = create_anonymous_session(label="pytest")
    anon_user.email = "pending@example.com"
    anon_user.save(update_fields=["email"])
    with pytest.raises(CommandError):
        call_command("claim_session", email="pending@example.com", all_anonymous=True)


@pytest.mark.django_db
def test_claim_session_dry_run_changes_nothing():
    anon_user, _session, _token = create_anonymous_session(label="pytest")
    Thread.objects.create(user=anon_user, title="A past session")
    target = User.objects.create_user(
        email="owner@example.com", is_anonymous_device=False
    )

    call_command(
        "claim_session", email="owner@example.com", all_anonymous=True, dry_run=True
    )

    assert Thread.objects.filter(user=target).count() == 0
    assert Thread.objects.filter(user=anon_user).count() == 1
