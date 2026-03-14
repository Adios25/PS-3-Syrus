"""
FLOW-JR-002: Health check service with per-dependency status and latency reporting.
"""
import asyncio
import time
import logging
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5.0


async def _timed(coro) -> tuple[str, float]:
    """Run a coroutine and return (status, latency_ms). Returns 'unhealthy' on timeout/error."""
    start = time.monotonic()
    try:
        await asyncio.wait_for(coro, timeout=_TIMEOUT_SECONDS)
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return "healthy", latency_ms
    except asyncio.TimeoutError:
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        logger.warning("Health check timed out after %.0fms", latency_ms)
        return "unhealthy", latency_ms
    except Exception as exc:  # noqa: BLE001
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        logger.warning("Health check failed: %s", exc)
        return "unhealthy", latency_ms


async def check_postgresql(db: AsyncSession) -> Dict[str, Any]:
    """Ping PostgreSQL with SELECT 1 and report latency."""
    status, latency = await _timed(db.execute(text("SELECT 1")))
    return {"status": status, "latency_ms": latency}


async def check_redis() -> Dict[str, Any]:
    """
    Mock Redis check.
    In production: use `aioredis` client ping.
    Redis is not included in the PS-03 docker-compose stack, so we return a mock healthy result.
    """
    return {"status": "healthy", "latency_ms": 0}


async def check_kafka() -> Dict[str, Any]:
    """
    Mock Kafka check.
    In production: use `aiokafka` AdminClient to list topics.
    Kafka is not included in the PS-03 docker-compose stack, so we return a mock healthy result.
    """
    return {"status": "healthy", "latency_ms": 0}


async def get_health_status(db: AsyncSession) -> Dict[str, Any]:
    """
    Aggregate all dependency checks and compute an overall status.
    Returns a dict matching FLOW-JR-002 acceptance criteria.
    """
    pg_result, redis_result, kafka_result = await asyncio.gather(
        check_postgresql(db),
        check_redis(),
        check_kafka(),
    )

    dependencies = {
        "postgresql": pg_result,
        "redis": redis_result,
        "kafka": kafka_result,
    }

    overall = (
        "healthy"
        if all(dep["status"] == "healthy" for dep in dependencies.values())
        else "unhealthy"
    )

    return {
        "status": overall,
        "dependencies": dependencies,
    }
