from django.urls import path

from .views import DeviceAuthView, MeView

urlpatterns = [
    path("auth/device", DeviceAuthView.as_view(), name="device-auth"),
    path("me", MeView.as_view(), name="me"),
]
