# ADR-0001 — KOSFintech Functional Modality Semantics

## CHANGE ID
KOS-DEV-0002

## Status
Accepted for engineering implementation

## Context

KOSFintech contains operational activities and services that may be
delivered, participated in, accessed, and evaluated through different
functional modes.

The existing `ChurchActivityDeliveryMode` vocabulary already provides six
delivery values:

- `physical`
- `online`
- `live_stream`
- `hybrid`
- `recorded`
- `on_demand`

A competing four-value modality enum would duplicate an existing
responsibility and create ambiguity between delivery characteristics and
participant behaviour.

The KOSFintech architecture is multi-tenant and multi-service. Therefore
modality semantics must be reusable across applicable services rather than
being defined independently by each service.

## Problem

The existing six delivery modes need an explicit architectural meaning
before they are used by additional CMOS and KOSFintech services.

Without a common semantic contract, implementations could incorrectly
treat:

- delivery as participation;
- recorded access as live attendance;
- access as an outcome;
- a hybrid activity as a participant modality;
- multiple modality events as multiple attendances.

These distinctions are architecturally consequential because later
attendance, learning-evidence, assessment, result, reporting, and other
service layers may depend upon them.

## Decision

KOSFintech SHALL retain the existing
`ChurchActivityDeliveryMode` six-value vocabulary.

No competing four-value modality enum SHALL be introduced.

The six existing delivery values have the following architectural
meanings:

| Delivery mode | Meaning |
|---|---|
| `physical` | Activity or service is delivered at a physical location. |
| `online` | Activity or service is delivered through an online environment. |
| `live_stream` | Activity or service is broadcast or delivered online in real time. |
| `hybrid` | The same activity is delivered through multiple delivery modes, such as physical and online/live-stream delivery. |
| `recorded` | Previously recorded activity or content is made available. |
| `on_demand` | Activity or content is made available for access when requested. |

The following four semantic dimensions SHALL remain distinct:

### 1. Delivery

Describes how or where an activity or service is made available.

The existing six-value `ChurchActivityDeliveryMode` vocabulary belongs to
this dimension.

### 2. Participation

Describes how or where a person engages with an activity or service.

Participation SHALL NOT be inferred solely from the activity's
`delivery_mode`.

### 3. Access

Describes how or where a person obtains or uses an available recorded,
offline, or otherwise accessible service or content.

Access SHALL NOT automatically establish participation or attendance.

### 4. Outcome

Describes an observable result produced or recorded by a service or
activity.

Outcome SHALL NOT be inferred merely from delivery, participation, or
access.

## Non-equivalence rules

The following distinctions are mandatory:

    Delivery != Participation
    Participation != Access
    Access != Outcome

In particular:

- `recorded` access SHALL NOT automatically constitute live attendance;
- `on_demand` access SHALL NOT automatically constitute live attendance;
- `hybrid` describes activity delivery and SHALL NOT be treated as a
  participant modality;
- changing participation modality during one functional activity SHALL
  NOT automatically create duplicate attendance;
- multiple modality events MAY belong to one participation context;
- delivery mode SHALL NOT be interpreted as a measure of spiritual worth,
  ecclesiastical rank, authority, divine standing, or similar status.

## CMOS application

CMOS SHALL use this architectural contract when implementing teaching,
preaching, attendance, learning evidence, assessment, results, progress,
content access, and related capabilities.

Attendance SHALL remain distinct from Learning Evidence.

Learning Evidence SHALL remain distinct from:

- Assessment
- Assessment Score
- Grade
- Result
- Progress
- Recognition/Testimony

Recognition or testimony MAY provide encouragement or controlled
visibility, but SHALL NOT be treated as a grade, result, or ecclesiastical
rank.

The system MAY record observable service events. It SHALL NOT claim that
such events measure a person's inner spiritual state or divine standing.

## Alternatives considered

### Alternative A — Introduce a new four-value modality enum

Rejected.

The proposed four-value vocabulary would overlap with the existing
`ChurchActivityDeliveryMode` responsibility and create two competing
representations of modality.

### Alternative B — Replace the existing six-value enum

Rejected.

The six-value vocabulary is already implemented in the ChurchActivity
domain and database schema. Replacing it would create unnecessary
migration and compatibility work without resolving the underlying semantic
distinctions.

### Alternative C — Keep the six values but leave their semantics implicit

Rejected.

Implicit semantics would allow different services to interpret delivery,
participation, access, and outcome inconsistently.

### Alternative D — Retain the six delivery values and establish separate
semantic dimensions

Accepted.

This preserves the existing implementation while establishing a reusable
KOSFintech-wide architectural contract.

## Consequences

### Positive

- Existing six-value delivery vocabulary is preserved.
- No competing modality enum is introduced.
- CMOS and future services can use common modality semantics.
- Attendance can remain distinct from recorded or on-demand access.
- Participation can evolve without changing activity delivery semantics.
- Observable outcomes can be modelled independently.
- Future modality events can be represented without automatically creating
  duplicate attendance records.

### Constraints

Implementations MUST NOT infer participation, attendance, access,
outcome, spiritual standing, or ecclesiastical status merely from
`delivery_mode`.

Services that require participant-level modality information SHOULD model
that information at the participation/access/event layer rather than
overloading `ChurchActivity.delivery_mode`.

## Affected components

Current:

- `models/church_activity.py`
- `repositories/church_activity_repository.py`
- `services/church_activity_service.py`
- `database.py`
- `tests/test_church_activity_repository.py`
- `tests/test_church_activity_service.py`

Future/application surfaces:

- CMOS attendance
- CMOS learning evidence
- CMOS assessment
- CMOS result/progress
- applicable KOSFintech teaching, preaching, training, content,
  communication, registration, giving, and other service-value activities

## Migration requirements

No database migration is required for this ADR.

The existing `church_activities.delivery_mode` column and six permitted
values remain unchanged.

Future participant-level modality implementation MUST be designed against
this ADR rather than introducing another delivery-mode vocabulary.

## Security impact

No direct authentication or authorization boundary is changed.

Existing tenant isolation, authorization, validation, auditing, and
confirmation requirements remain unchanged.

## Tenant-isolation impact

None.

All existing tenant boundaries remain applicable.

## Authority impact

None.

Modality records describe operational delivery, participation, access, or
observable outcomes. They do not establish ecclesiastical authority,
ordination, appointment, governance authority, or divine standing.

## Database impact

None for this ADR.

The existing `church_activities.delivery_mode` field remains the delivery
representation.

## Test impact

Regression tests SHALL verify:

1. all six existing delivery modes remain available;
2. their persisted values remain stable;
3. `hybrid` remains a delivery characteristic;
4. recorded and on-demand modes do not become attendance semantics merely
   through their enum values;
5. delivery mode remains distinct from participant-level semantics.

## Traceability

This ADR establishes the KOSFintech-wide functional modality contract
that subsequent CMOS and value-service implementations SHALL reference.

The implementation MUST preserve the existing six-value delivery
vocabulary unless a future architectural decision explicitly changes this
ADR.
