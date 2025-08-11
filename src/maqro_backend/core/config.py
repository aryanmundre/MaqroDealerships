import os 
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database URL - will use SUPABASE_DB_URL if available, fallback to DATABASE_URL
    database_url: Optional[str] = None
    supabase_db_url: Optional[str] = None

    # Supabase JWT secret for authentication
    supabase_jwt_secret: str

    # Vonage SMS Configuration
    vonage_api_key: Optional[str] = None
    vonage_api_secret: Optional[str] = None
    vonage_phone_number: Optional[str] = None

    rag_config_path: str = "config.yaml"
    rag_index_name: str = "vehicle_index"

    title: str = "Maqro Dearlership API"
    version: str = "0.1.0"
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }



settings = Settings()

