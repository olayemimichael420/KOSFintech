# KOSFintech Current Development Baseline

**Control System:** KOSFintech Development Workability Charter
**Control ID:** KOS-DEV-0001
**Baseline Purpose:** Establish the verified state inherited by every contributor.

---

## 1. VERIFIED GIT BASELINE

Commit:

    26e0744

Branch:

    main

Commit description:

    Implement platform authority and super admin transfer

This commit is the current verified source-code baseline unless a later
baseline is explicitly recorded.

---

## 2. VERIFIED TEST BASELINE

Python:

    Python 3.13.13

Test command:

    pytest -q

Verified result:

    104 passed

The existing passing test suite is part of the development contract.

A future change must not silently reduce or invalidate this baseline.

---

## 3. ESTABLISHED ARCHITECTURAL CAPABILITIES

The following capabilities have already been established and MUST be
inspected before creating alternatives:

- Configuration
- Database foundation
- Authentication
- Audit logging foundation
- Tenant-oriented data model
- Administration model
- School model
- User model
- Parent model
- Student model
- Teacher model
- Role model
- Permission model
- Administration authority
- Platform authority
- Authorization service
- Authority policy
- Super Admin transfer
- Repository layer
- Database foreign-key enforcement
- Automated regression tests
- Legacy implementation preservation

---

## 4. AUTHORITY ARCHITECTURE

Platform authority:

    models/platform_authority.py
    repositories/platform_authority_repository.py

Administration authority:

    models/administration_authority.py
    repositories/administration_authority_repository.py

Authorization:

    services/authorization_service.py
    policies/authority_policy.py

Super Admin transfer:

    services/super_admin_transfer_service.py

Audit:

    audit.py

Platform authority and administration authority are distinct architectural
responsibilities.

Do not merge or duplicate them without an explicit architectural decision.

---

## 5. DATABASE INTEGRITY BASELINE

The project has established foreign-key hardening across core relationships.

Relevant architectural work includes:

    49bdd65  Harden user role foreign key integrity
    37cbbae  Harden role permission foreign keys
    a249c3b  Harden user school foreign key
    2ce292a  Harden school student foreign key
    c092eda  Harden school teacher foreign key
    e7bf5d6  Harden parent school foreign key
    f1646a0  Harden teacher student foreign keys
    e6ea734  Enforce core user relationship foreign keys
    eba21d6  Enforce school admin foreign keys

These changes are part of the inherited database integrity architecture.

Do not weaken or replace these relationships without investigation and
explicit architectural justification.

---

## 6. TENANT ARCHITECTURE

KOSFintech is designed around tenant isolation.

The architecture must remain capable of supporting:

- individual communities
- schools
- organizations
- regional deployments
- national deployments
- global operations

Tenant boundaries must not be bypassed by new services, repositories,
handlers, AI tools, or administrative operations.

---

## 7. AI DEVELOPMENT SAFETY

AI-generated code is
 treated as development output, not as architectural authority.

AI agents MUST follow the same development-control process as human
contributors.

No AI-generated action may bypass:

- authorization
- tenant isolation
- validation
- auditing
- confirmation requirements

AI agents MUST inspect existing capabilities before generating replacements.

---

## 8. LEGACY CODE

Historical implementations are preserved as migration references.

Legacy code must not automatically be treated as the current production
implementation.

Before reusing legacy code, determine:

- why it was preserved;
- whether its responsibility already exists in the current architecture;
- whether its behaviour is still required;
- whether its dependencies remain valid.

---

## 9. REQUIRED CONTRIBUTOR SEQUENCE

Every consequential task follows:

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

Skipping the inspection phase is prohibited for consequential changes.

---

## 10. BASELINE PROTECTION

Before changing consequential code:

    1. Establish the current Git baseline.
    2. Run the existing test suite.
    3. Record the result.
    4. Inspect affected architecture.
    5. Make the smallest justified change.
    6. Run tests again.
    7. Compare against the baseline.
    8. Record the resulting state.

A newly passing test does not prove that a change is safe.

Existing protected behaviour must also remain intact unless intentionally
changed through an explicit architectural decision.

---

## 11. CURRENT DEVELOPMENT TASK

Control ID:

    KOS-DEV-0001

Task:

    Establish and enforce the KOSFintech Development Workability Charter.

Current status:

    Charter established and under operationalization.

Next objective:

    Convert the Charter into a practical shared control system that can be
    consumed consistently by human developers, AI agents, agencies, reviewers,
    and future maintainers.

---

## 12. SOURCE-OF-TRUTH RULE

When information conflicts, contributors must investigate the conflict.

Default hierarchy:

    1. Verified production code
    2. Automated tests
    3. Architecture Decision Records
    4. Development Workability Charter
    5. Current-state documentation
    6. Architecture documentation
    7. Change and handoff records
    8. Task descriptions, proposals, notes, and conversations

The hierarchy does not permit silently ignoring an architectural conflict.

Conflicts must be identified and resolved deliberately.

---

## 13. CONTRIBUTOR WARNING

DO NOT:

- create a replacement before searching for an existing capability;
- assume a capability is absent because its name is unfamiliar;
- weaken an existing test merely to obtain a green test suite;
- introduce a parallel authorization mechanism;
- bypass tenant isolation;
- bypass audit requirements;
- give AI-generated code elevated authority;
- silently change architectural responsibilities;
- leave consequential architectural knowledge only in conversation.

ALWAYS:

    SEARCH
    INSPECT
    UNDERSTAND
    REUSE
    EXTEND
    TEST
    RECORD
    HAND OFF

---

## 14. BASELINE UPDATE RULE

This file records a development baseline.

It MUST be updated when a new verified architectural baseline is formally
established.

Do not update the baseline merely because uncommitted experimental changes
exist.

A baseline represents a known, reviewable development state.

 treated as development output, not as architectural authority.

AI agents MUST follow the same development-control process as human
contributors.

No AI-generated action may bypass:

- authorization
- tenant isolation
- validation
- auditing
- confirmation requirements

AI agents MUST inspect existing capabilities before generating replacements.

---
