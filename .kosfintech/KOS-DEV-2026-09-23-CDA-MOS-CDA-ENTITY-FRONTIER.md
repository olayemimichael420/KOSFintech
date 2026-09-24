# KOSFintech CDA_MOS CDA Entity Capability Frontier

**Domain:** CDA_MOS
**Domain Name:** Community Development Association Management Operating System
**Domain Version:** v0.1.0
**Provisioning Contract:** DAPC v0.1
**Status:** DEVELOPMENTAL / EVIDENCE-BASED
**Production Dependency:** NONE
**Authority Effect:** NONE
**Implementation Status:** NOT IMPLEMENTED

## 1. Purpose

This artifact establishes the first semantic frontier for the Community Development Association entity within CDA_MOS.

It defines the minimum independently justified meaning of a CDA as the membership-bearing domain entity.

No production capability is created by this artifact.

## 2. CDA Identity

A Community Development Association is the domain entity to which CDA Membership relates.

The minimum established relationship is:

**Person**
→ **CDA Membership**
→ **Community Development Association**

The CDA entity SHALL remain distinct from:

- Tenant
- Administration
- InstitutionAnchor
- ServiceBinding
- Organizational Body
- Community Context
- Office / Position
- Project Team
- Application Role
- Permission
- Authority

## 3. Tenant Boundary

A CDA SHALL be tenant-bound within the KOSFintech platform boundary.

A CDA belonging to one tenant SHALL NOT be implicitly usable within another tenant.

Tenant isolation SHALL remain distinct from authorization.

A tenant relationship establishes application data scope, not CDA authority or leadership.

## 4. Minimum Identity Candidate

The minimum CDA identity candidate is:

- `id`
- `tenant_id`
- `name`
- `status`

These are candidate fields pending validation.

No additional identity field SHALL be introduced merely because another domain has an analogous field.

## 5. CDA Name

`name` is a candidate descriptive identifier for the CDA.

The semantic requirement for uniqueness of CDA name within a tenant remains unresolved.

The system SHALL NOT assume that two CDAs within the same tenant cannot share a name until CDA requirements establish that invariant.

Name equality SHALL NOT be treated as proof of entity identity.

## 6. CDA Status

CDA status requires explicit domain semantics.

Candidate states include:

- active
- inactive

The following remain unresolved and SHALL NOT be implemented without CDA requirements:

- pending
- suspended
- dissolved
- archived

CDA status represents the state of the CDA entity.

CDA status SHALL NOT automatically determine:

- membership status
- organizational-body status
- application authorization
- authority
- project status
- participation

## 7. Multiple CDAs Within Tenant

The frontier SHALL NOT assume one CDA per tenant.

Multiple CDAs MAY exist within the same tenant unless an explicit requirement establishes otherwise.

Any one-CDA-per-tenant invariant requires independent validation.

## 8. External Institutional Identity

`InstitutionAnchor` is classified as a PLATFORM_SHARED / REFERENCE capability.

It may record externally established institutional identity or provenance.

A CDA does not automatically require an `InstitutionAnchor`.

The following remain unresolved:

- external registration
- institutional provenance
- registration number
- government recognition
- community recognition
- another external identity

No external legal or governmental status SHALL be inferred from the CDA entity alone.

## 9. Administration Boundary

Existing `Administration` is a tenant-bound operational administration anchor.

CDA SHALL NOT replace `Administration`.

CDA SHALL NOT automatically become `AdministrationAuthority`.

`Administration` represents KOSFintech operational administration context.

CDA represents the CDA_MOS domain entity.

Chairperson, Executive Committee, Project Development Team, or another CDA structure SHALL NOT automatically become KOS application authority.

## 10. Community Context Boundary

CDA identity is distinct from Community Context.

The current candidate relationship is:

**Community Development Association**
→ operates within or relates to →
**Community Context**

Exact cardinality and lifecycle remain unresolved.

`community_context_id` is therefore not a mandatory CDA identity field at this frontier.

## 11. Organizational Structure Boundary

Organizational structure is a separate capability frontier.

A CDA may have:

- Organizational Bodies
- Offices / Positions
- Appointments / Designations
- Responsibilities
- Project Teams

These SHALL NOT be embedded in the minimum CDA identity.

CDA identity remains independent of internal organizational structure.

## 12. Membership Boundary

CDA is a membership-bearing entity.

Membership remains a separate relationship:

**Person**
→ **CDA Membership**
→ **CDA**

CDA identity SHALL NOT contain member identity directly.

Membership lifecycle, admission, status, temporal boundaries, and cardinality SHALL be governed by the CDA Membership Capability Frontier and CDA Membership Semantic Contract.

## 13. Person Boundary

`Person` is the platform-shared human identity.

CDA does not create a CDA-specific person.

The semantic distinction is:

- Person identifies the human.
- CDA identifies the association.
- Membership establishes the relationship.

## 14. Provenance Boundary

CDA MAY eventually require provenance if independently established.

Potential provenance concepts include:

- registration reference
- establishment reference
- recognition reference
- source organization
- formation record

These remain unresolved.

Provenance SHALL NOT be invented merely because `InstitutionAnchor` supports provenance.

## 15. Lifecycle Boundary

The following CDA lifecycle concepts remain unresolved:

- creation
- formation
- registration
- activation
- suspension
- inactivity
- dissolution
- archival
- reactivation
- succession
- merger
- separation / reorganization

No lifecycle transition SHALL be inferred from another MOS.

## 16. Semantic Boundary Register

The following distinctions SHALL remain explicit:

- CDA ≠ Tenant
- CDA ≠ Administration
- CDA ≠ InstitutionAnchor
- CDA ≠ ServiceBinding
- CDA ≠ Community Context
- CDA ≠ Organizational Body
- CDA ≠ Office
- CDA ≠ Project Team
- CDA ≠ Person
- CDA ≠ Membership
- CDA ≠ Participation
- CDA ≠ Authority
- CDA ≠ Authorization
- CDA ≠ Application Role
- Permission ≠ Authority
- Tenant Isolation ≠ Authorization
- Audit ≠ Provenance

## 17. Platform Capabilities Eligible for Reuse

Subject to DAPC v0.1, CDA_MOS may reuse platform capabilities including:

- Tenant
- Administration
- Administration context
- Person
- Authentication
- Authorization
- Permission Resolution
- Audit
- repository conventions
- service conventions
- application-service conventions
- handler conventions
- testing conventions

Reuse SHALL NOT import unrelated domain semantics.

## 18. Minimum Candidate Capability

The current developmental CDA identity candidate is:

CDA
├── id
├── tenant_id
├── name
└── status

This is a developmental semantic candidate and SHALL NOT be treated as a production schema.

## 19. Validation Requirements

Before production implementation:

- CDA identity semantics SHALL be independently validated.
- Tenant binding SHALL be validated.
- Multiple-CDAs-per-tenant behavior SHALL be explicitly determined.
- Name uniqueness SHALL be explicitly determined.
- Status semantics SHALL be explicitly determined.
- External provenance requirements SHALL be explicitly determined.
- Administration relationship SHALL remain distinct from CDA identity.
- Community Context SHALL remain distinct unless a direct relationship is established.
- Organizational Structure SHALL remain separate.
- Membership SHALL remain separate.
- Focused behavioral tests SHALL establish implemented semantics.
- Tenant-isolation tests SHALL pass.
- Semantic-boundary tests SHALL pass.
- Regression testing SHALL pass before checkpoint.

## 20. Current Frontier

The current semantic composition is:

**Tenant**
→ **CDA**
→ **CDA Membership**
→ **Person**

With separate CDA relationship candidates to:

- Community Context
- Organizational Body
- Office / Position
- Appointment / Designation
- Responsibility
- Initiative / Project
- Activity / Operational Event
- Meeting / Deliberative Event
- Participation

These are frontier-level relationship candidates and SHALL NOT be converted into production fields or tables without independent validation.

No automatic inheritance from SMOS or CMOS is established.

## 21. Status

**CDA_MOS CDA ENTITY FRONTIER: ESTABLISHED — DEVELOPMENTAL**

Production implementation remains unauthorized by this artifact.

Next controlled action: validate minimum CDA identity, status, tenant cardinality, and name uniqueness semantics before implementation.

Checkpoint: `KOS-DEV-2026-09-23-CDA-MOS-CDA-ENTITY-FRONTIER`
