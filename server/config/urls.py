from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("credits.urls")),
    path("api/v1/", include("learning.urls")),
    path("api/v1/", include("generation.urls")),
]
