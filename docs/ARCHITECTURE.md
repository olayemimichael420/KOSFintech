# KOSFintech Architecture

## Current Phase

Part 1 — Project Foundation.

## Architectural principle

The system is being migrated from the historical monolithic Telegram
implementation into a modular global community operations platform.

## Core layers

- Configuration
- Database
- Authentication
- Audit
- Domain models
- Business services
- Telegram handlers
- AI intelligence
- AI provider adapters
- Utilities
- Tests
- DevOps

## Legacy preservation

Historical implementations are preserved separately and are not
automatically imported into the production execution path.

They are migration references.

## Global architecture

The system is designed around tenant isolation so that the same
application architecture can support:

- individual communities
- schools
- organizations
- regional deployments
- national deployments
- global operations

without hard-coding the application to one geographic deployment.

## Security principle

No AI-generated action should bypass normal authorization,
tenant isolation, validation, auditing, or confirmation requirements.
