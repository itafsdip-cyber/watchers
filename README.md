# Watchers

Watchers is a local-first, open-source incident intelligence platform for public awareness.

## Safety Rules
- Public/open data only
- No private surveillance
- No targeting individuals
- Uncertainty must be visible
- Credibility must be transparent
- Public awareness use only

## Monorepo Layout

```text
Watchers/
  README.md
  .gitignore
  .env.example
  compose.yaml
  Makefile
  docs/
  apps/
    web/
    api/
    worker/
  data/
    samples/
    seeds/
  infra/
    scripts/
```

## Phase 1 Status
Phase 1 scaffolds local infra, env defaults, and service directories.

## Quick Start (Infra only)
```bash
cp .env.example .env
make up
```
