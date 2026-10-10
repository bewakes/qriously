from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission


class IsRegisteredUser(BasePermission):
    """Authenticated *and* logged in (not an unclaimed anonymous session).

    Guests may browse the offline samples, but metered generation is gated
    behind a real account so tokens are never spent anonymously.
    """

    message = "login_required"

    def has_permission(self, request: Any, view: Any) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return not getattr(user, "is_anonymous_device", True)
