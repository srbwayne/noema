"""First deterministic relevance realization: normalized exact task-content match."""

import unicodedata

from noema.cognition.application.runtime_content_reference_authority import (
    RuntimeContentReferenceAuthority,
)
from noema.cognition.domain.context_composition import ContextCandidate


def _normalize(payload: str) -> str:
    """Unify line endings (CRLF, then CR, to LF) and apply Unicode NFC only."""
    return unicodedata.normalize("NFC", payload.replace("\r\n", "\n").replace("\r", "\n"))


def _has_substantive_content(normalized: str) -> bool:
    """Return whether ``normalized`` contains at least one non-whitespace character."""
    return any(not character.isspace() for character in normalized)


class NormalizedExactTaskContentRelevanceAuthority:
    """Judge a candidate relevant exactly when its content equals the current task's.

    ADR-0041's ``NORMALIZED_EXACT_TASK_CONTENT_MATCH`` realization. It
    structurally satisfies ``ContextRelevanceAuthority``. Both the current
    task payload and every candidate payload are resolved through the bound
    ``RuntimeContentReferenceAuthority`` and normalized only by line-ending
    unification (CRLF, then remaining CR, to LF) followed by Unicode NFC --
    no NFKC, casefolding, stripping, whitespace collapse, or punctuation
    removal.

    If the normalized task payload has no substantive (non-whitespace)
    content, no candidate content is resolved and every candidate receives
    ``None``. Otherwise each candidate receives ``1.0`` when its normalized
    payload is substantive and exactly equal to the normalized task payload,
    and ``None`` in every other case. No other candidate attribute (age,
    position, provenance, trust, sensitivity, authority, zone, size, or slice
    type) is consulted. Any resolution failure propagates unchanged and no
    partial result is returned.
    """

    __slots__ = ("_runtime_content_authority",)

    def __init__(self, *, runtime_content_authority: RuntimeContentReferenceAuthority) -> None:
        """Bind the runtime content authority used to resolve task and candidate content."""
        if not isinstance(runtime_content_authority, RuntimeContentReferenceAuthority):
            raise TypeError("runtime_content_authority must be a RuntimeContentReferenceAuthority")
        self._runtime_content_authority = runtime_content_authority

    def judge(
        self,
        *,
        task_ref: str,
        candidates: tuple[ContextCandidate, ...],
    ) -> tuple[float | None, ...]:
        """Return ``1.0`` per exactly matching candidate and ``None`` otherwise, in order."""
        task_content = _normalize(self._runtime_content_authority.resolve(content_ref=task_ref))
        if not _has_substantive_content(task_content):
            return tuple(None for _ in candidates)

        results: list[float | None] = []
        for candidate in candidates:
            candidate_content = _normalize(
                self._runtime_content_authority.resolve(
                    content_ref=candidate.context_slice.content_ref
                )
            )
            if not _has_substantive_content(candidate_content):
                results.append(None)
            elif candidate_content == task_content:
                results.append(1.0)
            else:
                results.append(None)
        return tuple(results)
