import pytest
from django.contrib.auth import get_user_model

from learning.models import Node
from learning.services import (
    create_node,
    create_thread,
    descendant_ids,
    remove_subtree,
)

User = get_user_model()


@pytest.fixture
def thread(db):
    return create_thread(User.objects.create_user(), title="Why is the sky blue?")


@pytest.fixture
def tree(thread):
    root = create_node(thread, "root", title="Why is the sky blue?")
    a = create_node(thread, "dive", parent=root, anchor_text="A")
    b = create_node(thread, "dive", parent=root, anchor_text="B")
    a1 = create_node(thread, "define", parent=a, anchor_text="A1")
    return {"root": root, "a": a, "b": b, "a1": a1}


def test_create_thread_snapshots_default_lens(thread):
    assert thread.lens_bucket == "basics:solid:plain:curious"
    assert thread.lens["depth"] == "solid"


def test_root_node_points_to_itself(thread):
    root = create_node(thread, "root")
    assert root.root_id == root.id
    assert root.parent_id is None
    assert root.depth == 0


def test_child_node_inherits_root_and_depth(tree):
    assert tree["a"].root_id == tree["root"].id
    assert tree["a"].parent_id == tree["root"].id
    assert tree["a"].depth == 1
    assert tree["a1"].depth == 2


def test_node_lens_defaults_to_thread_and_can_override(tree, thread):
    assert tree["a"].lens_bucket == thread.lens_bucket
    deep = create_node(thread, "dive", parent=tree["root"], lens={"depth": "deep"})
    assert deep.lens_bucket == "basics:deep:plain:curious"


def test_descendant_ids_include_self_and_subtree(tree):
    ids = set(descendant_ids(tree["a"]))
    assert ids == {tree["a"].id, tree["a1"].id}


def test_descendant_ids_for_root_cover_everything(tree):
    ids = set(descendant_ids(tree["root"]))
    assert ids == {node.id for node in tree.values()}


def test_remove_subtree_removes_only_descendants(tree, thread):
    remove_subtree(tree["a"])
    remaining = set(thread.nodes.values_list("id", flat=True))
    assert tree["a"].id not in remaining
    assert tree["a1"].id not in remaining
    assert {tree["root"].id, tree["b"].id} <= remaining
    assert Node.objects.filter(id=tree["root"].id).exists()
