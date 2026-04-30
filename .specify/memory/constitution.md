<!--
SYNC IMPACT REPORT
==================
Version change: [template] → 1.0.0 (initial ratification)
Modified principles: N/A (initial creation)
Added sections: Core Principles (5), Technology Stack Constraints, Development Workflow, Governance
Removed sections: N/A
Templates requiring updates:
  ✅ plan-template.md — Constitution Check section references this document; no structural change needed
  ✅ spec-template.md — Aligns with test-first and layered architecture principles; no change needed
  ✅ tasks-template.md — Tests marked OPTIONAL in template; constitution mandates tests for backend
                         features. Note: keep OPTIONAL label in template but spec authors MUST require
                         tests for all backend user stories per Principle III.
Deferred TODOs: none
-->

# Personal To-Do Manager Constitution

## Core Principles

### I. Layered Architecture

Route handlers MUST be thin: validate input, delegate to a service, return the response.
Business logic MUST live in `services/`. Database access MUST live in repositories or
direct SQLAlchemy session calls within services — never in route handlers.
No DB calls in routers. No business logic in repositories.

**Rationale**: Keeps each layer independently testable and prevents logic from leaking
across tiers as the codebase grows.

### II. Security by Design

All list and task endpoints MUST enforce `user_id` ownership on every read and write.
Cross-account resource access MUST return **404** (not 403) to avoid leaking resource
existence to unauthorized callers.

Auth tokens MUST use HMAC-SHA256 signing via `core/security.py`. No third-party JWT
libraries. The session cookie name is `ptm_session` and MUST be HTTP-only.

`TEST_AUTH_ENABLED` MUST NEVER be set to `true` in any production or staging environment.
The `/auth/test-login` endpoint is exclusively for local development.

**Rationale**: Private personal data requires strict ownership isolation. 404-on-miss is an
intentional security choice that must not be weakened to a 403.

### III. Test-First (NON-NEGOTIABLE)

Every new backend feature MUST have pytest tests written before implementation.
Tests run against in-memory SQLite via `conftest.py`. The `login()` helper from `conftest.py`
MUST be used to authenticate before any resource call in tests.

Every new frontend feature MUST have Vitest + Testing Library tests.

Red-Green-Refactor cycle is mandatory: tests fail → implement → tests pass.

**Rationale**: Prevents regressions in auth/ownership logic and API contracts. In-memory
SQLite keeps tests fast and self-contained without a running database.

### IV. Schema Discipline

SQLAlchemy ORM models (`models/`) and Pydantic schemas (`schemas/`) MUST remain separate.
ORM models MUST NOT be returned directly from route handlers.

Every change to `backend/app/models/` MUST be followed by running the `check-migration`
agent before committing. A migration MUST exist for every model change; commits without
a matching migration are not allowed.

All ORM models MUST use SQLAlchemy 2.0 async conventions and inherit `TimestampMixin`
from `models/base.py` where timestamps are relevant.

**Rationale**: Mixing ORM and schema layers causes silent data leaks and tightly couples
the DB schema to the API contract.

### V. Simplicity (YAGNI)

This is a private personal MVP. Features MUST be justified by a concrete user need.
No premature abstractions: three similar lines are better than a forced helper.
No over-engineering for hypothetical scale or future requirements.

New dependencies require explicit justification. Prefer standard library and already-present
dependencies over adding new ones.

**Rationale**: Personal projects accumulate unnecessary complexity quickly. Keeping the
codebase small makes it easier to maintain solo.

## Technology Stack Constraints

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL
- **Frontend**: React 18+, TypeScript, Vite, Vitest + Testing Library
- **Auth**: Google OpenID Connect, GitHub OAuth, HMAC-SHA256 signed session tokens
- **Infrastructure**: Docker Compose for local PostgreSQL; no cloud infra required for local dev
- **Real-time**: FastAPI WebSocket endpoint only — no third-party message brokers

Technology substitutions (e.g., replacing SQLAlchemy, switching auth library) MUST be
treated as a constitution amendment and require a MAJOR version bump.

## Development Workflow

Before any commit:
- Backend: `cd backend && pytest` MUST pass
- Frontend: `cd frontend && npm test` MUST pass; `npm run build` MUST succeed
- Model changes: `check-migration` agent MUST be run; a migration MUST exist

Local dev startup order:
1. `docker compose up -d postgres`
2. `cd backend && alembic upgrade head`
3. `cd backend && uvicorn app.main:app --reload`
4. `cd frontend && npm run dev`

The `/check-all` skill runs the full pre-commit suite and SHOULD be run before opening
a pull request.

## Governance

This constitution supersedes all other project practices documented in `CLAUDE.md`,
`README.md`, or inline code comments when conflicts arise.

Amendments MUST:
1. Update this file with a version bump following semantic versioning rules.
2. Propagate changes to relevant templates under `.specify/templates/`.
3. Update `CLAUDE.md` if the amendment changes commands, architecture, or auth rules.

Versioning policy:
- **MAJOR**: Backward-incompatible governance changes, principle removal, or redefinition.
- **MINOR**: New principle or section added; materially expanded guidance.
- **PATCH**: Clarifications, wording, typo fixes.

All feature plans (`/speckit-plan`) MUST include a Constitution Check gate that validates
compliance with Principles I–V before any implementation begins.

**Version**: 1.0.0 | **Ratified**: 2026-04-30 | **Last Amended**: 2026-04-30
