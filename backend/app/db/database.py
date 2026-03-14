from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

_DEFAULT_PG = "postgresql+asyncpg://ps03user:ps03password@localhost:5432/ps03db"
_RAW_URL = os.getenv("DATABASE_URL", _DEFAULT_PG)

# Use SQLite for local dev when Postgres is not configured
if _RAW_URL == _DEFAULT_PG:
    DATABASE_URL = "sqlite+aiosqlite:///./ps03_local.db"
    _CONNECT_ARGS = {"check_same_thread": False}
else:
    DATABASE_URL = _RAW_URL
    _CONNECT_ARGS = {}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_CONNECT_ARGS)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

