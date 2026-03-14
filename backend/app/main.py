from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.api.deps import get_db
from app.services.health_check import get_health_status

app = FastAPI(title="PS-03 Backend API", version="0.1.0")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "ok", "service": "ps03-backend"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    FLOW-JR-002: Enhanced health check endpoint.
    Returns overall status and per-dependency (PostgreSQL, Redis, Kafka) connectivity.
    Always returns HTTP 200; overall 'status' field is 'unhealthy' when any dependency fails.
    """
    result = await get_health_status(db)
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return result
