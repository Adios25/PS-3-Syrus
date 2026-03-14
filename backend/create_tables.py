"""One-time script to create all DB tables for local SQLite dev."""
import asyncio
from app.db.database import engine, Base
# Import models so SQLAlchemy registers them
from app.db.models import User, ChecklistItem  # noqa: F401

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created in local SQLite DB (ps03_local.db)")

asyncio.run(main())
