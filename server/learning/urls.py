from django.urls import path

from .api import (
    NodeCreateView,
    NodeDetailView,
    NoteDetailView,
    NoteListCreateView,
    OutlineView,
    ThreadCreateView,
    ThreadDetailView,
)

urlpatterns = [
    path("threads", ThreadCreateView.as_view(), name="threads"),
    path("threads/<uuid:thread_id>", ThreadDetailView.as_view(), name="thread"),
    path(
        "threads/<uuid:thread_id>/nodes",
        NodeCreateView.as_view(),
        name="thread-nodes",
    ),
    path(
        "threads/<uuid:thread_id>/notes",
        NoteListCreateView.as_view(),
        name="thread-notes",
    ),
    path(
        "threads/<uuid:thread_id>/outline",
        OutlineView.as_view(),
        name="thread-outline",
    ),
    path("nodes/<uuid:node_id>", NodeDetailView.as_view(), name="node"),
    path("notes/<uuid:note_id>", NoteDetailView.as_view(), name="note"),
]
