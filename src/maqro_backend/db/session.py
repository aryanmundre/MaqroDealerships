from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus

# Construct the Supabase DB URL from individual environment variables
SUPABASE_USER = os.getenv("SUPABASE_USER")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
SUPABASE_HOST = os.getenv("SUPABASE_HOST")
SUPABASE_PORT = os.getenv("SUPABASE_PORT")
SUPABASE_DBNAME = os.getenv("SUPABASE_DBNAME")

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL and all([SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_HOST, SUPABASE_DBNAME]):
    encoded_password = quote_plus(SUPABASE_PASSWORD)
    DATABASE_URL = (
        f"postgresql+asyncpg://"
        f"{SUPABASE_USER}:{encoded_password}"
        f"@{SUPABASE_HOST}:{SUPABASE_PORT or 5432}/{SUPABASE_DBNAME}"
    )

if not DATABASE_URL:
    raise ValueError("Database connection URL is not set. Please set SUPABASE_DB_URL or individual SUPABASE_* variables.")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=0,
    pool_pre_ping=True,
    execution_options={
        "compiled_cache": {},
    },
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "server_settings": {
            "application_name": "maqro_backend",
        }
    },
)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()