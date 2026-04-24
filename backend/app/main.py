from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.routes import audit, health, share

app = FastAPI(
    title="Compliance Audit Engine",
    description="AI-powered business compliance audit API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(share.router, prefix="/api/v1")

# Lambda handler
handler = Mangum(app, lifespan="off")
