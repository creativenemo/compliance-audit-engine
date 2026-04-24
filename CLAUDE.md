# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered compliance audit engine. Accepts business intake forms, runs parallel checks against federal watchlists/databases/state registrations, generates plain-English compliance reports with scores in under 60 seconds. Greenfield — only PRD exists as of project start.

## Planned Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14+ (App Router, TypeScript), Tailwind CSS, shadcn/ui, TanStack Query |
| Backend | Python 3.12, FastAPI + Mangum, AWS Lambda (serverless) |
| Queue | AWS SQS FIFO |
| State/Cache | AWS DynamoDB (job status, report JSON, 24h TTL) |
| Storage | AWS S3 (raw API snapshots, PDFs, OFAC/LEIE indexes) |
| AI | Amazon Nova Pro/Lite via AWS Bedrock |
| Scraping | Playwright-Python in Lambda container |
| Infra | AWS CDK (TypeScript or Python) |

## Development Commands

These will be set up in Sprint 1; use these as the target conventions:

**Backend**
```bash
make install    # install Python deps
make dev        # uvicorn with hot reload
make test       # pytest
make lint       # ruff + mypy
make deploy     # AWS CDK deploy
```

**Frontend**
```bash
npm install
npm run dev
npm run build
npm test
npm run lint
```

## Architecture

### Async Job Flow
`POST /api/v1/audit` → enqueue SQS message → Lambda orchestrator pulls message → runs 10 pipeline steps (parallel where possible via `asyncio.gather`) → writes each step result to DynamoDB → frontend polls `GET /api/v1/audit/{job_id}/status` every 2 seconds.

### Data Pipeline Steps (orchestrator Lambda, 5-min timeout)
1. SAM.gov Entity API — federal contractor registration
2. trade.gov Consolidated Screening List — 13 government watchlists
3. OFAC SDN local index — US Treasury sanctions (S3-hosted, nightly refresh)
4. HHS OIG LEIE local index — Medicare/Medicaid exclusions (S3-hosted, monthly refresh)
5. SEC EDGAR — public filings, enforcement actions
6. IRS EO BMF / ProPublica — nonprofit/tax-exempt status
7. SOS scraping (domicile state) — entity registration, registered agent, annual report due
8. SOS scraping (employee states, parallel) — foreign qualification checks
9. Nova web search — industry-specific license requirements
10. Nova report synthesis — full report generation

### Local Index Strategy
OFAC SDN and HHS OIG LEIE are downloaded on cron (nightly/monthly), stored as searchable JSON in S3. Lookups run against these local copies — no rate limits, zero latency, no third-party dependency at query time.

### Two-Step Nova Pattern
Fast Nova Micro/Lite call for risk classification → full Nova Lite/Pro call for complete report. All findings must cite specific JSON source fields; no hallucination permitted.

### SOS Scraping Rollout
- **Tier 1 (Sprint 4)**: DE, WY, FL, CO, IL, VA, TN, WA, DC
- **Tier 2**: CA, TX, NY, NV, OR, GA, NC, OH, PA
- **Tier 3**: remaining states

## API Endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | /api/v1/audit | API key |
| GET | /api/v1/audit/{job_id}/status | API key |
| GET | /api/v1/audit/{job_id}/report | API key |
| GET | /api/v1/audit/{job_id}/pdf | API key |
| GET | /api/v1/audit/{job_id}/share | URL token |
| GET | /api/v1/health | None |

## Scoring Model

| Component | Weight |
|-----------|--------|
| Entity Status | 25% |
| Federal Compliance | 25% |
| Sanctions & Watchlists | 20% |
| Tax Exposure | 20% |
| License Status | 10% |

Badge thresholds: green ≥80, amber 60–79, red 40–59, dark-red <40.

## Reference Test Case

**Embark Aviation Corp** — Delaware domicile, 7 employee states, professional services. Used throughout PRD as primary validation target. All pipeline tests should produce a valid report for this entity.

## Sprint Roadmap

| Sprint | Weeks | Gate |
|--------|-------|------|
| 1 | 1–2 | POST /audit returns job_id |
| 2 | 3–4 | Federal layer live |
| 3 | 5–6 | Full report for public companies |
| 4 | 7–8 | Embark Aviation report complete |
| 5 | 9–10 | First paying customer |
| 6 | 11–12 | Public launch |

## Key Constraints

- Free public APIs only at MVP — no paid data vendors
- PII (name, email) stored separately from report data
- Raw API snapshots: 90-day retention → auto-delete
- Completed reports: 1-year retention, API key access only
- Lambda IAM: least-privilege per function
- Input validation via Pydantic (backend), inline validation on blur (frontend)
