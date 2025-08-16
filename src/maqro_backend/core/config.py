import os 
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database URL - will use SUPABASE_DB_URL if available, fallback to DATABASE_URL
    database_url: Optional[str] = None
    supabase_db_url: Optional[str] = None

    # Supabase JWT secret for authentication
    supabase_jwt_secret: str

    # Vonage SMS Configuration (Legacy - keeping for transition)
    vonage_api_key: str | None = None
    vonage_api_secret: str | None = None
    vonage_phone_number: str | None = None

    # WhatsApp Business API Configuration
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_webhook_verify_token: str | None = None
    whatsapp_app_secret: str | None = None
    whatsapp_api_version: str = "v21.0"

    rag_config_path: str = "config.yaml"
    rag_index_name: str = "vehicle_index"

    title: str = "Maqro Dearlership API"
    version: str = "0.1.0"
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }



settings = Settings()

