from django.urls import path

from .api import DeviceAuthView, LoginStartView, LoginView, LogoutView, MeView

urlpatterns = [
    path("auth/device", DeviceAuthView.as_view(), name="device-auth"),
    path("auth/login/start", LoginStartView.as_view(), name="login-start"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
]
