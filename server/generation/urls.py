from django.urls import path

from .api import GenerateView, generate_stream_view

urlpatterns = [
    path("generate", GenerateView.as_view(), name="generate"),
    path(
        "generate/<uuid:job_id>/stream",
        generate_stream_view,
        name="generate-stream",
    ),
]
