# SMOS Governance Quest — Decision State Semantics

**Status:** PROPOSED — DEVELOPMENT CONTROL ARTIFACT
**Constitutional authority:** NOT CREATED BY THIS DOCUMENT
**Executable authorization:** NOT GRANTED BY THIS DOCUMENT
**Role:** Define the semantic relationship between Governance Quest gates and Decision Gate states

---

## 1. PURPOSE

This document defines how the four permitted Decision Gate states apply to consequential questions evaluated through the Governance Quest.

The four states are:

- ACCEPT
- DECLINE
- REJECT
- PENDING

The Governance Quest defines what must be evaluated.

The Decision Gate Protocol defines the permitted decision states.

This document defines their semantic relationship.

---

## 2. NON-CREATION OF AUTHORITY

Nothing in this document:

- creates constitutional authority;
- transfers constitutional authority;
- delegates constitutional authority;
- creates amendment authority;
- creates jurisdiction;
- creates executable authorization;
- establishes constitutional effect.

A semantic classification is not itself a source of authority.

---

## 3. TWO-DIMENSIONAL MODEL

The Governance Quest and Decision Gate Protocol operate on separate dimensions.

### Dimension A — Gate

The question being evaluated:

1. Eligibility
2. Qualification
3. Authority
4. Mandate
5. Execution

### Dimension B — Decision State

The result of evaluating that question:

1. ACCEPT
2. DECLINE
3. REJECT
4. PENDING

Therefore:

```text
GATE ≠ DECISION STATE

A gate identifies **what is being evaluated**.

A decision state identifies **the result of that evaluation**.

Neither dimension independently creates authority.

---

## 4. STATE SEMANTICS BY GATE

| Gate | ACCEPT | DECLINE | REJECT | PENDING |
|---|---|---|---|---|
| Eligibility | Eligible | Relationship not adopted | Relationship disqualified | Eligibility unresolved |
| Qualification | Conditions satisfied | Qualification not adopted | Conditions disqualifying | Qualification unresolved |
| Authority | Authority requirement satisfied | Authority not adopted | Authority absent/invalid | Authority unresolved |
| Mandate | Mandate established | Function not adopted | Mandate invalid/unauthorized | Mandate unresolved |
| Execution | Execution may proceed only if all required authorization, dependency, scope, and jurisdiction conditions are satisfied | Do not execute | Execution prohibited | Execution blocked |

These states remain subordinate to the applicable authority framework.

---

## 5. ACCEPT

ACCEPT means:

> The specific question has passed the applicable decision gate.

ACCEPT does **not** mean:

- constitutional authority has been created;
- authorization has automatically been granted;
- execution is automatically permitted;
- a higher unresolved dependency has been resolved;
- a prior limitation has been removed.

Therefore:

```text
ACCEPT
  ≠
EXECUTABLE AUTHORIZATION

ACCEPT permits progression only to the next applicable gate or condition.

---

## 6. DECLINE

DECLINE means the proposition is not adopted within the applicable decision boundary.

DECLINE does not necessarily establish that the proposition is invalid or prohibited. It does not create authority, authorization, or an alternative permission.

Therefore:

```text
DECLINE = NON-ADOPTION
```

---

## 7. REJECT

REJECT means the proposition is disqualified within the applicable decision boundary.

Possible grounds include:

- invalid premise;
- prohibited scope;
- incompatible rule;
- absent required authority;
- invalid delegation;
- failed mandatory condition;
- another established disqualifying condition.

Therefore:

```text
REJECT = DISQUALIFIED
```

REJECT shall not be converted into ACCEPT through administrative preference, software configuration, or technical override.

---

## 8. PENDING

PENDING means the question cannot yet legitimately be resolved.

Typical causes include:

- unresolved authority;
- unresolved dependency;
- insufficient evidence;
- unresolved jurisdiction;
- unresolved scope;
- unresolved mandate;
- unresolved interpretation;
- conflicting records requiring determination.

Therefore:

```text
PENDING = NO PROCEED
```

PENDING shall never be interpreted as implicit ACCEPT.

---

## 9. DOWNSTREAM PROPAGATION

A downstream question SHALL inherit all mandatory unresolved conditions from upstream questions.

```text
UPSTREAM = PENDING
        ↓
DEPENDENT QUESTION = PENDING
        ↓
EXECUTION = BLOCKED
```

An upstream ACCEPT does not automatically produce downstream ACCEPT.

---

## 10. DECISION-TO-AUTHORIZATION SEPARATION

The system SHALL maintain a distinct boundary between:

```text
QUESTION
   ↓
GATE EVALUATION
   ↓
DECISION STATE
   ↓
AUTHORITY DETERMINATION
   ↓
AUTHORIZATION
   ↓
EXECUTION
```

A decision record may establish the result of a question without establishing authority to execute its consequences.

---

## 11. SERVICE DELIVERY RULE

For scalable service delivery, validly resolved questions SHOULD be reusable within their established scope without unnecessary repetition.

Reuse remains subject to:

- scope;
- jurisdiction;
- validity period;
- dependency status;
- evidence status;
- authority status;
- authorization requirements.

If a mandatory condition changes, reevaluation SHALL occur where required.

---

## 12. FAST-PATH PRINCIPLE

Where all applicable gates and authorization conditions are satisfied, the service path SHOULD proceed without unnecessary re-litigation of settled questions.

Conceptually:

```text
DECISION = ACCEPT
AND MANDATORY DEPENDENCIES = SATISFIED
AND AUTHORITY = ESTABLISHED
AND AUTHORIZATION = ESTABLISHED
AND SCOPE = VALID
        ↓
EXECUTION MAY PROCEED
```

Otherwise:

```text
EXECUTION = BLOCKED
```

---

## 13. NO IMPLIED STATE

No informal system value shall be treated as one of the four decision states merely because it appears favorable.

Examples include:

```text
TRUE
YES
APPROVED
QUALIFIED
VERIFIED
ACTIVE
READY
```

These may be attributes or intermediate results. They do not automatically mean ACCEPT and none independently means AUTHORIZED.

---

## 14. MACHINE-READABLE CONCEPT

A future implementation may represent a decision record as:

```text
question_id:
gate:
decision:
basis:
evidence:
authority:
dependencies:
scope:
authorization:
execution_status:
timestamp:
review_condition:
```

This representation does not become a constitutional source merely because software stores or processes it.

---

## 15. FINAL SEMANTIC RULE

The Governance Quest answers:

```text
WHAT MUST BE EVALUATED?
```

The Decision Gate Protocol answers:

```text
WHAT DECISION STATES ARE PERMITTED?
```

This document answers:

```text
WHAT DOES EACH STATE MEAN AT EACH GATE?
```

Therefore:

```text
GATE
  ↓
EVALUATION
  ↓
DECISION STATE
  ↓
DEPENDENCY CHECK
  ↓
AUTHORITY CHECK
  ↓
AUTHORIZATION CHECK
  ↓
EXECUTION
```

No layer may silently become another layer.

**End of Decision State Semantics**
