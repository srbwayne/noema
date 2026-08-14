from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from noema.cognition.domain.errors import InvalidCognitiveItemError
from noema.cognition.domain.workspace import CognitiveItem, CognitiveItemKind, WorkspaceRegion


def cognitive_item() -> CognitiveItem:
    return CognitiveItem(
        kind=CognitiveItemKind.OBSERVATION,
        content_ref="observation:current",
        region=WorkspaceRegion.ACTIVE_CONTEXT,
        relevance=0.5,
        salience=0.6,
        activation=0.7,
    )


def item_with_score(name: str, value: float) -> CognitiveItem:
    item = cognitive_item()
    if name == "relevance":
        return replace(item, relevance=value)
    if name == "salience":
        return replace(item, salience=value)
    return replace(item, activation=value)


def test_cognitive_item_is_created_with_automatic_id() -> None:
    item = cognitive_item()

    assert item.item_id
    assert item.kind is CognitiveItemKind.OBSERVATION
    assert item.content_ref == "observation:current"
    assert item.region is WorkspaceRegion.ACTIVE_CONTEXT


def test_cognitive_items_receive_distinct_ids() -> None:
    assert cognitive_item().item_id != cognitive_item().item_id


@pytest.mark.parametrize("content_ref", ["", "   ", "\t\n"])
def test_cognitive_item_rejects_empty_content_reference(content_ref: str) -> None:
    with pytest.raises(InvalidCognitiveItemError, match="content_ref"):
        replace(cognitive_item(), content_ref=content_ref)


@pytest.mark.parametrize("score_name", ["relevance", "salience", "activation"])
@pytest.mark.parametrize("value", [0.0, 1.0])
def test_cognitive_item_accepts_score_boundaries(score_name: str, value: float) -> None:
    assert item_with_score(score_name, value)


@pytest.mark.parametrize("score_name", ["relevance", "salience", "activation"])
@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_cognitive_item_rejects_scores_outside_range(score_name: str, value: float) -> None:
    with pytest.raises(InvalidCognitiveItemError, match=score_name):
        item_with_score(score_name, value)


def test_cognitive_item_created_at_is_timezone_aware_utc() -> None:
    created_at = cognitive_item().created_at

    assert created_at.tzinfo is UTC
    assert created_at.utcoffset() == UTC.utcoffset(created_at)


def test_cognitive_item_is_immutable() -> None:
    item = cognitive_item()

    with pytest.raises(FrozenInstanceError):
        item.content_ref = "observation:changed"


def test_cognitive_item_has_structural_equality() -> None:
    item_id = uuid4()
    created_at = datetime.now(UTC)
    fields = {
        "kind": CognitiveItemKind.GOAL,
        "content_ref": "goal:primary",
        "region": WorkspaceRegion.WORKING_STATE,
        "relevance": 1.0,
        "salience": 0.8,
        "activation": 0.9,
        "item_id": item_id,
        "created_at": created_at,
    }

    assert CognitiveItem(**fields) == CognitiveItem(**fields)
