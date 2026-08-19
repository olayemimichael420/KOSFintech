# KOSFintech Development Workability Charter

**Control ID:** KOS-DEV-0001  
**Status:** ACTIVE  
**Applies to:** Human developers, AI agents, development agencies, reviewers, maintainers, and future contributors  
**Scope:** Entire KOSFintech repository and all derivative development work

---

# 1. PURPOSE

This Charter establishes the common development-control system for KOSFintech.

Its purpose is to ensure that every human and AI development participant:

- understands what already exists before changing it;
- builds upon verified work instead of unknowingly duplicating it;
- preserves architectural intent;
- maintains tenant isolation and security boundaries;
- protects existing behaviour through automated tests;
- records consequential architectural changes;
- leaves sufficient information for the next contributor to continue safely.

KOSFintech is an evolving system. No contributor should assume that a capability is absent merely because it is not immediately visible.

The governing principle is:

> **SEARCH BEFORE CREATING.  
> REUSE BEFORE REPLACING.  
> EXTEND BEFORE DUPLICATING.  
> TEST BEFORE DECLARING COMPLETE.  
> RECORD BEFORE HANDING OFF.**

---

# 2. NON-NEGOTIABLE DEVELOPMENT CYCLE

Every consequential development task follows:

```text
INSPECT
   ↓
UNDERSTAND
   ↓
PLAN
   ↓
CHANGE
   ↓
TEST
   ↓
RECORD
   ↓
HANDOFF

# 3. SOURCE-OF-TRUTH HIERARCHY

When information appears to conflict, contributors MUST investigate the conflict rather than silently choosing one source.

The default hierarchy is:

1. Verified production code
2. Automated tests
3. Architecture Decision Records (ADRs)
4. Development Workability Charter
5. Current-State documentation
6. Architecture documentation
7. Change records and handoff records
8. Task descriptions, proposals, notes, or conversations

If intended architecture differs from implemented architecture, the difference MUST be explicitly identified and resolved through an architectural decision.

---

# 4. READ-BEFORE-CODE RULE

No contributor may begin implementation of a non-trivial feature without first inspecting the relevant existing implementation.

At minimum, inspect:

- repository structure;
- relevant models;
- relevant repositories;
- relevant services;
- relevant policies;
- relevant tests;
- database schema;
- current-state documentation;
- applicable architectural decisions;
- recent changes affecting the target area.

The contributor must establish:

```text
What already exists?
Where does it live?
What tests protect it?
What depends on it?
Why was it designed this way?
What would my change affect?

---

# 5. CHANGE IDENTIFICATION AND TRACEABILITY

Every consequential change MUST be identifiable.

A contributor must be able to answer:

- What changed?
- Why did it change?
- Which files changed?
- Which existing capability was extended, corrected, or replaced?
- Which tests demonstrate the change?
- Which architectural assumptions remain unchanged?
- Which architectural assumptions changed?
- What should the next contributor know?

Changes MUST NOT be hidden inside unrelated refactoring.

Where practical, changes should be organized so that one logical architectural change corresponds to one clearly identifiable commit.

Commit messages SHOULD describe the architectural purpose of the change rather than merely the files modified.

---

# 6. NO SILENT REPLACEMENT RULE

An existing implementation MUST NOT be replaced merely because a contributor prefers a different implementation.

Before replacement, the contributor MUST determine:

1. Why the existing implementation exists.
2. Which tests depend upon it.
3. Which services, repositories, models, policies, handlers, or integrations depend upon it.
4. Whether the proposed implementation provides a genuine architectural improvement.
5. Whether an Architecture Decision Record is required.

If replacement is justified, the old capability MUST be explicitly identified as replaced, migrated, deprecated, or removed.

There must be no silent parallel implementation of the same responsibility.

---

# 7. TEST BASELINE RULE

The current passing test suite is part of the development contract.

Before a consequential change:

```text
RUN BASELINE TESTS
        ↓
RECORD BASELINE
        ↓
MAKE CHANGE
        ↓
RUN TESTS AGAIN
        ↓
COMPARE RESULTS

A contributor MUST NOT declare a change complete merely because a newly added test passes.

The contributor must verify that existing protected behaviour remains intact.

If tests fail after a change, the contributor MUST determine whether:

- the implementation is defective;
- the test is outdated;
- the architectural contract intentionally changed; or
- an unrelated regression was introduced.

A failing test MUST NOT simply be deleted or weakened to obtain a green result.

---

# 8. ARCHITECTURAL DECISION RULE

An Architecture Decision Record (ADR) SHOULD be created when a change:

- introduces a new architectural layer;
- changes an established responsibility;
- changes authority or permission boundaries;
- changes tenant-isolation behaviour;
- changes database ownership or relationship rules;
- replaces an established implementation;
- introduces a new external dependency;
- changes security-sensitive behaviour;
- changes AI authority or tool-execution boundaries;
- creates a new system-wide convention.

An ADR records the decision, not merely the implementation.

At minimum it should identify:

- Context
- Problem
- Decision
- Alternatives considered
- Consequences
- Affected components
- Migration requirements, where applicable

---

# 9. TENANT AND AUTHORITY SAFETY

No development contribution may weaken established tenant isolation, authentication, authorization, validation, auditing, or confirmation requirements without an explicit architectural decision.

Authority must be derived from the established authority model and authorization policies.

Contributors MUST NOT create an independent authorization mechanism when an existing authorization capability already governs the affected operation.

Platform authority and administration authority MUST remain conceptually distinct unless an explicit architectural decision establishes otherwise.

AI-generated actions are subject to exactly the same security boundaries as human-generated actions.


---

# 10. CHANGE IDENTIFICATION AND TRACEABILITY

Every consequential development change MUST have a traceable identity.

The purpose of change identification is to allow any contributor, reviewer,
AI agent, or development agency to determine:

- what changed;
- why it changed;
- who or what initiated the change;
- which architectural area was affected;
- which files or components were modified;
- which tests were executed;
- what the resulting baseline is;
- whether an architectural decision was required;
- what the next contributor needs to know.

A change MUST NOT exist only in informal conversation, memory, or an
unrecorded instruction.

## 10.1 Change Identifier

Consequential changes SHOULD use a unique identifier such as:

    KOS-DEV-0001
    KOS-DEV-0002
    KOS-DEV-0003

The identifier MUST remain stable once assigned.

The identifier may be referenced by:

- Git commits;
- pull requests;
- ADRs;
- change records;
- test reports;
- handoff records;
- issue trackers;
- AI-agent task instructions.

## 10.2 Change Scope

Before implementation, the contributor SHOULD identify:

    CHANGE ID:
    PURPOSE:
    AFFECTED DOMAIN:
    EXISTING COMPONENTS:
    EXPECTED FILES:
    DEPENDENCIES:
    SECURITY IMPACT:
    TENANT-ISOLATION IMPACT:
    AUTHORITY IMPACT:
    DATABASE IMPACT:
    TEST IMPACT:
    ADR REQUIRED: YES / NO

The scope is an initial declaration and may be updated when inspection
reveals additional affected components.

## 10.3 Change Trace

After implementation, the contributor MUST be able to trace:

    Change ID
        ↓
    Source requirement
        ↓
    Existing implementation inspected
        ↓
    Planned modification
        ↓
    Modified files
        ↓
    Tests executed
        ↓
    Result
        ↓
    Git commit
        ↓
    Handoff information

This trace prevents a future contributor from having to reconstruct the
reason for a change solely from source-code archaeology.

## 10.4 Git Relationship

Git remains the authoritative record of the actual source-code change.

The Charter does not replace Git.

Instead, the Charter establishes the discipline required to make Git history
architecturally understandable.

Commit messages for consequential changes SHOULD reference the applicable
KOS change identifier.

Example:

    KOS-DEV-0007 Implement administration permission management

A commit MUST NOT be treated as proof that the architectural decision was
correct merely because the commit exists.

Code, tests, architectural decisions, and change records serve different
purposes and must remain distinguishable.

---


---
# 11. EXISTING CAPABILITY AND DEPENDENCY MAP

Before introducing a new capability, contributors MUST determine whether an
equivalent or related capability already exists anywhere in the repository.

The existence of a capability may be distributed across multiple layers,
including:

- models;
- repositories;
- services;
- policies;
- authentication;
- authorization;
- database schema;
- handlers;
- AI services;
- utilities;
- tests;
- configuration;
- legacy migration references.

A capability MUST be considered existing if the repository already contains
a working or intentionally established implementation of the relevant
responsibility, even if that implementation is incomplete or located in
another architectural layer.

## 11.1 Capability Search

Before creating a new component, the contributor SHOULD search for:

    Capability name
    Related terminology
    Existing class names
    Existing function names
    Database tables
    Repository methods
    Service methods
    Policy rules
    Tests
    Configuration entries
    Historical implementations

The search result MUST be considered before implementation begins.

## 11.2 Existing Capability Record

For consequential work, the contributor SHOULD record:

    REQUESTED CAPABILITY:
    EXISTING CAPABILITY FOUND: YES / NO

    EXISTING LOCATION:
    EXISTING OWNER/LAYER:
    RELATED MODELS:
    RELATED REPOSITORIES:
    RELATED SERVICES:
    RELATED POLICIES:
    RELATED DATABASE TABLES:
    RELATED TESTS:

    DECISION:
        REUSE
        EXTEND
        REFACTOR
        REPLACE
        CREATE NEW

    JUSTIFICATION:

The purpose is not bureaucracy. The purpose is to make the architectural
reasoning visible to the next human or AI contributor.

## 11.3 Dependency Awareness

Before modifying an established component, contributors MUST consider
its known dependants.

At minimum, inspect:

    Direct imports
    Repository consumers
    Service consumers
    Policy consumers
    Database relationships
    Tests
    Configuration
    Handlers
    AI/tool integrations

A component MUST NOT be modified in isolation when the modification can
affect an established dependency.

## 11.4 Ownership of Responsibilities

Every major capability SHOULD have one identifiable architectural owner.

For example:

    Authentication
        -> Authentication layer

    Authorization
        -> Authorization service + authority policy

    Platform authority
        -> Platform authority model/repository

    Administration authority
        -> Administration authority model/repository

    Audit
        -> Audit foundation

    Persistence
        -> Database/repository layer

The presence of multiple files does not automatically mean multiple owners.
The responsibility boundary must remain clear.

## 11.5 Duplicate Implementation Prohibition

Contributors MUST NOT create a second implementation of an existing
responsibility merely because:

- the existing implementation was not immediately found;
- another contributor
prefers a different naming convention;
- an AI agent generated an alternative implementation;
- an external agency uses a different architecture;
- the existing implementation appears inconvenient;
- a task description does not mention the existing implementation.

If an existing implementation is inadequate, the contributor MUST first
evaluate whether it should be extended or refactored.

Creating a replacement requires explicit justification and, where
architecturally consequential, an ADR.

## 11.6 Capability Map as Shared Memory

The capability map is part of the KOSFintech development memory.

It exists so that a new contributor does not have to rediscover the entire
architecture through source-code archaeology.

When a consequential capability is created, moved, replaced, or materially
changed, the relevant capability documentation SHOULD be updated.

The objective is:

    DISCOVER ONCE
        ↓
    RECORD
        ↓
    REUSE
        ↓
    KEEP THE KNOWLEDGE AVAILABLE

No contributor should knowingly allow important architectural knowledge
to exist only inside an individual's memory or inside a single AI session.

---

