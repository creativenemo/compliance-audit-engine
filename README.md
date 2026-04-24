# Compliance Audit Engine

AI-powered business compliance audit. One intake form → federal watchlists, state registrations, tax exposure, industry licenses → compliance report with score in under 60 seconds.

## Quick Start

### Backend (Python 3.12)
```bash
cd backend
make install
make dev          # API at http://localhost:8000
make test
make lint
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev       # UI at http://localhost:3000
```

### Infrastructure (AWS CDK)
```bash
cd infrastructure
npm install
npx cdk synth     # validate CloudFormation (no deploy)
```

## Architecture

- **Frontend**: Next.js 14, Tailwind CSS, TanStack Query
- **Backend**: FastAPI + Mangum on AWS Lambda
- **Queue**: AWS SQS FIFO → orchestrator Lambda
- **State**: DynamoDB (jobs + step results)
- **AI**: Amazon Nova via AWS Bedrock
- **IaC**: AWS CDK (TypeScript)

## Test Entity

**Embark Aviation Corp** — Delaware domicile, 7 employee states (VA, FL, CO, IL, TN, WA, DC), professional services, B2B + Government.

## Sprint Status

| Sprint | Status | Gate |
|--------|--------|------|
| 1 | ✅ Complete | POST /audit returns job_id |
| 2 | Stub | Federal data layer |
| 3 | Stub | Nova report synthesis |
| 4 | Stub | SOS scrapers (Tier 1) |
| 5 | Stub | PDF + share links |
| 6 | Stub | Public launch |
