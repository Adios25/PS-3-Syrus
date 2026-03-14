from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PS-03 Backend API"
    DATABASE_URL: str = "postgresql+asyncpg://ps03user:ps03password@localhost:5432/ps03db"
    REDIS_URL: str = "redis://localhost:6379"
    AGENT_URL: str = "http://localhost:8001"
    SECRET_KEY: str = "change_this_for_production"
    ALGORITHM: str = "HS256"

    model_config = ConfigDict(env_file=".env")

settings = Settings()

