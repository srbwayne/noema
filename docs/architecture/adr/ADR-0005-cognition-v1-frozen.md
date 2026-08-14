# ADR-0005: COGNITION V1 Frozen Architecture

- Status: Accepted
- Date: 2026-08-13

## Context

The COGNITION V1 architecture has already been approved. Unrecorded structural changes would undermine a stable implementation target.

## Decision

The COGNITION V1 architecture is considered frozen. Structural modifications require an explicit architectural decision.

The frozen component set is:

- Cognitive Workspace
- Attention Engine
- Situation Model
- Epistemic Model
- Cognitive Mode Arbiter
- REFLEX
- FAST
- DELIBERATE
- DEEP
- Reasoning Engine
- Planner
- World Model
- Prediction / Counterfactual
- Evaluation Engine
- Verification Engine
- Confidence Engine
- Context Composer
- Cognitive Budget
- Cognitive Interrupts
- Cognitive Checkpoints
- Anti-loop / stagnation detection

This ADR freezes the structure; it does not specify or implement the components.

## Consequences

- Implementations must conform to the approved component boundaries.
- A proposed structural modification requires a new or superseding ADR and explicit review.
- M0 creates only the foundation and does not preempt component design with speculative code.
