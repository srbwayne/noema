"""Runtime-instance authority resolving task-input content by reference."""


class RuntimeContentReferenceConflictError(Exception):
    """Raised when a reference already denotes a different exact payload.

    A ``content_ref`` may be registered more than once, but it may never be
    made to denote more than one exact payload value over its runtime-local
    lifetime: once a reference has been established to mean one payload, a
    later registration attempt for the same reference with a different
    payload is a conflict, not a replacement. The message identifies the
    reference only -- never the existing or attempted payload text.
    """


class RuntimeContentReferenceNotFoundError(Exception):
    """Raised when resolving a reference no prior registration established.

    This authority performs no fallback lookup of any kind: a reference that
    was never registered during this runtime instance's lifetime has no
    resolvable payload, and this is always reported explicitly rather than
    through ``None`` or an empty string (a registered empty-string payload
    must remain distinguishable from a reference that was never registered
    at all). The message identifies the reference only -- there is no
    payload to expose for a reference that does not resolve.
    """


class RuntimeContentReferenceAuthority:
    """Associate opaque content references with exact task-input payloads.

    One instance is the canonical content authority for exactly one runtime
    instance's lifetime (ADR-0028-adjacent runtime-instance scoping): it
    performs no I/O, uses no external resource, and disappears when the
    runtime object graph that owns it becomes unreachable. Two independently
    constructed instances share no state, even when given the same
    ``content_ref`` string to register.

    A reference denotes exactly one payload for the lifetime of this
    authority. Registering the same reference with the same exact payload a
    second time is an idempotent no-op; registering it with a different
    payload is a conflict, never a silent replacement -- there is no update,
    delete, or replace operation. Resolution is a pure observation: it
    never mutates this authority's state and never falls back to any other
    source (Situation, process transport, memory, or otherwise) when a
    reference is unregistered.
    """

    __slots__ = ("_content_by_ref",)

    def __init__(self) -> None:
        """Start with no registered associations."""
        self._content_by_ref: dict[str, str] = {}

    def register(self, *, content_ref: str, payload: str) -> None:
        """Establish that ``content_ref`` denotes the exact ``payload``.

        Rejects a non-``str`` ``content_ref`` or ``payload`` with
        ``TypeError`` before any state changes; neither argument is checked
        for blankness, coerced, or otherwise transformed. If ``content_ref``
        is not yet registered, this establishes the association. If it is
        already registered with this exact ``payload``, this is a no-op. If
        it is already registered with a different payload, this raises
        ``RuntimeContentReferenceConflictError`` and leaves the existing
        association completely unchanged.
        """
        if not isinstance(content_ref, str):
            raise TypeError("content_ref must be a str")
        if not isinstance(payload, str):
            raise TypeError("payload must be a str")

        if content_ref not in self._content_by_ref:
            self._content_by_ref[content_ref] = payload
            return
        if self._content_by_ref[content_ref] == payload:
            return
        raise RuntimeContentReferenceConflictError(
            f"content_ref already denotes a different payload: {content_ref!r}"
        )

    def resolve(self, *, content_ref: str) -> str:
        """Return the exact payload registered for ``content_ref``.

        Rejects a non-``str`` ``content_ref`` with ``TypeError``. Raises
        ``RuntimeContentReferenceNotFoundError`` if ``content_ref`` was never
        registered during this authority's lifetime. Never mutates this
        authority's state and never falls back to any other source.
        """
        if not isinstance(content_ref, str):
            raise TypeError("content_ref must be a str")
        if content_ref not in self._content_by_ref:
            raise RuntimeContentReferenceNotFoundError(
                f"content_ref is not registered: {content_ref!r}"
            )
        return self._content_by_ref[content_ref]
