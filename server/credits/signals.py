from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.constants import SIGNUP_GRANT

from . import services
from .models import Reason


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def provision_wallet_on_signup(sender, instance, created, **kwargs):
    if not created:
        return
    wallet = services.provision_wallet(instance)
    if SIGNUP_GRANT > 0:
        services.grant(
            wallet,
            SIGNUP_GRANT,
            reason=Reason.SIGNUP_GRANT,
            idempotency_key=f"signup-grant:{instance.pk}",
        )
