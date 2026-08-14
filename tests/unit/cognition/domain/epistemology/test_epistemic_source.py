from dataclasses import FrozenInstanceError

import pytest

from noema.cognition.domain.epistemology import EpistemicSource, EpistemicSourceType
from noema.cognition.domain.errors import InvalidEpistemicSourceError


def test_epistemic_source_is_valid() -> None:
    source = EpistemicSource(
        source_type=EpistemicSourceType.TOOL,
        source_ref="tool:git-status:request-123",
    )

    assert source.source_type is EpistemicSourceType.TOOL
    assert source.source_ref == "tool:git-status:request-123"


@pytest.mark.parametrize("source_type", ["tool", 1, None])
def test_epistemic_source_rejects_invalid_source_type(source_type: object) -> None:
    with pytest.raises(InvalidEpistemicSourceError, match="source_type"):
        EpistemicSource(source_type=source_type, source_ref="source:reference")  # type: ignore[arg-type]


@pytest.mark.parametrize("source_ref", ["", "   ", "\t\n"])
def test_epistemic_source_rejects_empty_reference(source_ref: str) -> None:
    with pytest.raises(InvalidEpistemicSourceError, match="source_ref"):
        EpistemicSource(
            source_type=EpistemicSourceType.DOCUMENT,
            source_ref=source_ref,
        )


def test_epistemic_source_is_immutable() -> None:
    source = EpistemicSource(
        source_type=EpistemicSourceType.USER,
        source_ref="user:operator",
    )

    with pytest.raises(FrozenInstanceError):
        source.source_ref = "user:changed"
