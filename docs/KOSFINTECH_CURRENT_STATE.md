# KOSFintech Current Development State

> READ THIS BEFORE MODIFYING THE KOSFintech CODEBASE.

## Current Development Phase

Part 1 — Project Foundation / Architecture Stabilization

## Current Verified Baseline

Test suite:
87 passed

## Current Repository Structure

- Configuration
- Database
- Authentication
- Audit
- Domain models
- Repositories
- Business services
- Authorization policies
- Tests
- Telegram handlers
- AI integration
- Utilities
- Legacy migration references

## Established Capabilities

The following capabilities already exist and MUST be inspected before
creating replacements:

- Core SQLite database foundation
- Tenant-oriented data model
- Administration model
- School model
- User model
- Parent model
- Student model
- Teacher model
- Role and permission models
- Administration authority model
- Platform authority model
- Authorization service
- Authority policy
- Super Admin transfer service
- Audit logging foundation
- Database foreign-key enforcement
- Repository layer
- Automated regression tests
- Legacy implementation preservation

## Current Authority Architecture

Platform authority:
    platform_authorities

Administration authority:
    administration_authorities

Authorization:
    services/authorization_service.py
    policies/authority_policy.py

Super Admin transfer:
    services/super_admin_transfer_service.py

Audit:
    audit.py

## Development Rule

Do NOT create a second implementation of an existing capability without
an explicit architectural decision.

## Current Baseline

The verified test baseline is:

    87 passed

Any subsequent architectural change must preserve or intentionally
update this baseline.

## Next Development Control Task

KOS-DEV-0001

Establish and enforce the KOSFintech Development Workability Charter.
