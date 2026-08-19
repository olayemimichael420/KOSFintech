# KOSFintech Capability Map

**Control System:** KOSFintech Development Workability Charter  
**Control ID:** KOS-DEV-0001  
**Purpose:** Provide a rapid architectural map so contributors can locate
existing capabilities before creating, replacing, or duplicating them.

---

## 1. HOW TO USE THIS MAP

Before implementing a capability:

1. Search this map for the relevant responsibility.
2. Inspect the referenced source files.
3. Inspect the referenced tests.
4. Inspect dependencies and database relationships.
5. Reuse, extend, refactor, or replace only after investigation.
6. Update this map when a consequential capability is added or its ownership
   changes.

The map is a navigation aid.

It does NOT override verified production code or automated tests.

---

## 2. CORE ARCHITECTURAL CAPABILITIES

| Capability | Primary Location | Supporting Location | Protected By |
|---|---|---|---|
| Configuration | `config.py` | `.env`, `.env.example` | configuration/foundation tests |
| Database foundation | `database.py` | `data/` | database tests |
| Authentication | `auth.py` | user models/repositories | authentication-related tests |
| Audit | `audit.py` | audit tests | `tests/test_audit.py` |
| Tenant-oriented model | `models/` | repositories | relationship/integrity tests |
| Authorization | `services/authorization_service.py` | `policies/authority_policy.py` | authorization tests |
| Platform authority | `models/platform_authority.py` | `repositories/platform_authority_repository.py` | platform authority tests |
| Administration authority | `models/administration_authority.py` | `repositories/administration_authority_repository.py` | administration authority tests |
| Super Admin transfer | `services/super_admin_transfer_service.py` | platform authority repository | transfer service tests |
| Domain persistence | `repositories/` | `models/` | repository tests |
| Telegram integration | `handlers/`, `bot.py` | legacy references | integration tests where applicable |
| AI integration | `ai/` | configuration/services | AI-related tests where applicable |
| Health checks | `utils/health.py` | database/configuration | foundation tests |
| Legacy migration | `legacy/` | historical implementations | migration documentation |

---

## 3. DOMAIN MODELS

Existing domain models include:

```text
models/
├── administration.py
├── administration_authority.py
├── authority.py
├── parent.py
├── parent_school.py
├── parent_student.py
├── permission.py
├── platform_authority.py
├── role.py
├── role_permission.py
├── school.py
├── school_admin.py
├── school_student.py
├── school_teacher.py
├── student.py
├── teacher.py
├── teacher_student.py
├── user.py
├── user_role.py
└── user_school.py
