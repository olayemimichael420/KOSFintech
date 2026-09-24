# KOS-DEV-2026-09-24 — CIT_MOS Technology-Service Architectural Direction

**Artifact:** KOS-DEV-2026-09-24-CIT-MOS-TECHNOLOGY-SERVICE-ARCHITECTURAL-DIRECTION.md
**Domain:** CIT_MOS — Computer and Information Technology Management Operating System
**DAPC:** v0.1
**Status:** DEVELOPMENTAL / ARCHITECTURAL DIRECTION
**Production Dependency:** NONE
**Authority Effect:** NONE
**Implementation Status:** NOT IMPLEMENTED

## 1. Purpose

This artifact records the selected developmental architectural direction for CIT_MOS following comparative examination of KOSFintech provenance, historical development-control records, current operational engineering structures, DSL evidence, and the established CIT_MOS evidence frontier.

The direction is deliberately broader than a programmer-management system.

CIT_MOS is selected as an independent **Technology Service Operating System** within the KOSFintech ecosystem.

## 2. Selected Architectural Direction

The selected direction is:

> CIT_MOS shall be developed as an independent technology-service operating domain capable of organizing and supporting technology-service environments and service delivery, with Software Development Engineering as its first operational service pipeline and DSL-Oriented Development Engineering as its first specialized operational capability.

This is a developmental architectural decision.

It does not by itself establish production entities, database schemas, permissions, authority, workflows, or implementation.

## 3. Ecosystem Position

The intended ecosystem relationship is:

KOS -> KOSFintech -> SMOS / CMOS / CDA_MOS / CIT_MOS

Each MOS remains independently bounded.

CIT_MOS is not the semantic parent of SMOS, CMOS, CDA_MOS, or future MOS domains.

SMOS, CMOS, and CDA_MOS provide comparative engineering evidence only where correspondence is independently established.

## 4. Central Operational Concept

The programmer/development environment is interpreted as one important use of a broader technology-service environment.

The central concept is:

Technology-Service Environment -> Technology-Service Tenant -> Technology Services -> Development Service -> Software Development Engineering -> DSL-Oriented Development Engineering

The tenant represents an independently scoped operational/service boundary.

It does not represent a person by definition.

## 5. Tenant and Subject Boundary

A CIT_MOS service tenant may eventually support different subject arrangements, including:

Individual
Institution
Individual + Institution

These are candidate service-subject arrangements, not yet implemented identity semantics.

The following distinctions are preserved:

Tenant != Person
Tenant != Developer
Tenant != Institution
Tenant != Project
Tenant != Work Unit

A programmer, developer, engineering organization, or institution may potentially participate in or receive technology services without becoming identical to the tenant boundary.

## 6. First Service Pipeline

Software Development Engineering is selected as the first operational service pipeline because the historical KOSFintech development-control lineage provides substantial evidence for an actual controlled development operating process.

The established development grammar is:

Requirement -> Baseline -> Capability Inspection -> Development Decision -> Change Scope -> Implementation -> Tests / Verification -> Evidence -> Git Commit -> Handoff -> Continuity

This demonstrates an operational requirement substantially broader than providing a programmer with a coding workspace.

## 7. Development-Service Requirement

The selected developmental requirement is:

> Provide a controlled technology-development service environment through which development participants can undertake consequential development work from requirement through verified implementation and recorded handoff, while preserving architectural continuity, responsibility, security boundaries, and traceability.

This requirement is derived from established provenance.

It is not presented as a historical CIT_MOS implementation.

## 8. DSL-Oriented Development Engineering

DSL-Oriented Development Engineering remains the initial specialized operational capability within the Software Development Engineering pipeline.

Its role is to support controlled semantic specification, recurring engineering correspondence, validation, synchronization, and development coordination.

The DSL remains independent of CIT_MOS.

Therefore:

CIT_MOS != DSL
Software Development Engineering != DSL
Development Environment != DSL
DSL != Production Authorization
DSL Representation != Domain Reality

The DSL Resource Base remains developmental and does not acquire production dependency or authority from this architectural direction.

## 9. Why This Direction Fits KOSFintech

The broader KOS vision is directed toward a universal system of human Acts/service-value exchange across fields of human endeavour.

KOSFintech therefore benefits from having a technology-service domain that can eventually support the people and institutions responsible for building, maintaining, verifying, and delivering those services.

CIT_MOS can consequently serve two complementary purposes:

1. provide the technology-development environment required to build the KOSFintech ecosystem itself; and
2. eventually provide technology services to external or future technology-service participants.

This prevents the development environment from becoming a private implementation mechanism attached only to the current programmer.

It gives the environment a domain-level purpose consistent with the broader service-value architecture.

## 10. Relationship to Existing Engineering Evidence

Existing KOSFintech structures such as Person, tenant-scoped User, ServiceRequest, ServiceAct, provider/recipient relationships, assignments, authorization, audit, verification, and lifecycle services are recognized as engineering evidence.

They are not automatically promoted into CIT_MOS semantics.

The governing distinction remains:

Engineering Evidence != CIT_MOS Domain Meaning

Existing mechanisms may be reused only after their correspondence to an independently established CIT_MOS requirement is demonstrated.

## 11. Required Future Semantic Investigation

The following concepts now have a clear reason to be investigated, but remain semantically unresolved:

- Technology-Service Environment
- CIT_MOS Tenant
- Technology-Service Relationship
- Development Service
- Development Participant
- Developer capacity
- Engineering Office
- Engineering Service Unit
- Engineering Official
- Development Project
- Development Work Unit
- Assignment
- Technical Responsibility
- Development Evidence
- Handoff
- Development-Service lifecycle
- Service provider/recipient relationship
- CIT_MOS-specific authorization
- DSL-oriented engineering operations
- DSL maturation/onboarding

The existence of this list does not authorize implementation.

## 12. Semantic Safety Rules

The following boundaries remain mandatory:

Domain != Platform
Platform != Service Provider
Service Provider != Service Pipeline
Service Pipeline != Tenant
Tenant != Identity
Identity != Capacity
Capacity != Responsibility
Responsibility != Authority
Assignment != Authority
Authorization != Authority
Implementation != Validation
Validation != Authorization
Similarity != Equivalence
Pattern != Domain Meaning
DSL != Domain

No unresolved concept becomes executable merely because it is useful, recurring, conventional, or technically implementable.

## 13. Implementation Boundary

This architectural direction authorizes no production implementation.

It does not authorize creation of:

- CIT_MOS tenant tables;
- developer entities;
- engineering offices;
- engineering units;
- projects;
- work units;
- assignments;
- responsibility records;
- service lifecycles;
- CIT_MOS roles;
- CIT_MOS permissions;
- repositories;
- application services;
- handlers;
- APIs; or
- executable DSL constructs.

Those require subsequent semantic evidence and the applicable implementation gates.

## 14. Development Posture

The selected direction changes the **architectural investigation target**, not the production implementation state.

The next work should proceed through:

Architectural Direction -> Independent Semantic Evidence -> Minimum Semantic Contract -> Engineering Correspondence -> Validation -> Implementation Readiness -> Production Implementation

No stage may be silently skipped.

## 15. Current Decision

**SELECTED DEVELOPMENTAL DIRECTION:**

CIT_MOS is to be investigated and progressively developed as the independent **Technology Service Operating System** of the KOSFintech ecosystem.

Its first operational service pipeline is:

Software Development Engineering

Its first specialized operational capability is:

DSL-Oriented Development Engineering

The programmer/developer environment is therefore treated as a principal use case within CIT_MOS rather than the definition of CIT_MOS itself.

## 16. Status

**Architectural Direction:** SELECTED — DEVELOPMENTAL

**CIT_MOS Semantic Contract:** NOT YET ESTABLISHED

**Production Model:** NOT IMPLEMENTED

**Production Dependency:** NONE

**Authority Effect:** NONE

**Next Requirement:** Independently establish the minimum semantics required to represent a technology-service environment and its first development-service pipeline.

## 17. Continuity

This artifact does not rewrite the historical Development Workability Charter, KOS-DEV-0003, CIT_MOS domain declaration, platform/tenant frontier, service-pipeline evidence closure, or CIT_MOS evidence closure.

Those records remain historical or evidentiary sources according to their respective status.

This artifact records the current architectural direction selected after comparative evidence review.

The repository remains authoritative for live engineering state, while the KOSFintech Continuity Corpus preserves project continuity and historical context.
