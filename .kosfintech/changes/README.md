# KOSFintech Development Change Records

This directory contains the historical change records for consequential
KOSFintech development work.

Every consequential change MUST have a unique KOS-DEV identifier.

The identifier connects:

    Requirement
        ↓
    Baseline
        ↓
    Capability inspection
        ↓
    Development decision
        ↓
    Change scope
        ↓
    Implementation
        ↓
    Tests
        ↓
    Git commit
        ↓
    Handoff

## Record Rules

1. One consequential change receives one stable KOS-DEV identifier.
2. The identifier MUST NOT be reused.
3. The completed record MUST remain traceable to its Git commit.
4. The record MUST identify the baseline from which the work began.
5. The record MUST identify tests executed before and after the change.
6. The record MUST identify affected architectural areas.
7. The record MUST identify whether an ADR was required.
8. The record MUST identify the next contributor's required context.
9. Completed records MUST NOT be silently rewritten.
10. Corrections to historical records MUST be explicitly identified.

## Naming Convention

Use:

    KOS-DEV-0001.md
    KOS-DEV-0002.md
    KOS-DEV-0003.md

The filename MUST match the change identifier.

## Relationship to the Handoff Template

`.kosfintech/HANDOFF_TEMPLATE.md` is the reusable template.

This directory contains actual task-specific historical records.

Do not modify the template to record an individual task.

## Status Lifecycle

A consequential change may progress through:

    NEW
    ↓
    INSPECTING
    ↓
    PLANNED
    ↓
    IMPLEMENTING
    ↓
    TESTING
    ↓
    VERIFIED
    ↓
    HANDED OFF
    ↓
    CLOSED

The status must reflect the actual state of the work.

## Source of Truth

The Development Workability Charter remains the governing development
control document.

Git remains authoritative for the actual source-code state.

Change records provide the architectural and procedural trace connecting
the requirement, decision, implementation, tests, commit, and handoff.
