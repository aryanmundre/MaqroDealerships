import os 
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Use lightweight SQLite database by default for local development.
    # Override with real Postgres URL in the environment once you are ready
    # (e.g. export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/maqro_dealership").
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    
    rag_config_path: str = "config.yaml"
    rag_index_name: str = "vehicle_index"

    title: str = "Maqro Dearlership API"
    version: str = "0.1.0"

    class Config:
        env_file = ".env"


settings = Settings()

