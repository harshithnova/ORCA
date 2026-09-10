# DEVELOPMENT WORKFLOW

## Branches

- `feature/frontend`
- `feature/ai-agents`
- `feature/data-providers`
- `feature/reasoning-safety`
- `feature/backend-integration`

Main branch:
`main`

## Ownership

Person 5 owns integration/release and keeps main runnable.

## Workflow

1. Pull latest `main`.
2. Work only inside your owned area.
3. Read contracts before changing shared structures.
4. Add/update tests.
5. Run tests locally.
6. Update documentation if behavior changes.
7. Open PR.
8. Explain contract or safety impact.
9. Integrate only after review.

## Commit style

Examples:

```text
feat: add marine provider adapter
feat: add candidate spatial filtering
fix: block restricted candidate
test: add stale safety data case
docs: update data contract
```

## Shared-contract changes

Do not independently change:
- API response shape
- data field names
- status enums
- safety semantics
- provider schema

Discuss the change with affected owners first.

## AI coding agent workflow

Before coding:
- read `AGENTS.md`
- identify role ownership
- inspect existing code
- reuse existing interfaces
- avoid restructuring the repository without approval

After coding:
- test
- review generated code
- check imports/types
- check provenance
- check safety behavior
- update docs where necessary

## Secrets

Never commit:
- API keys
- passwords
- tokens
- private credentials

Use environment variables and `.env.example`.
