from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
import os
import ssl

# Supabase Direct Connection Configuration (Following Official Guidance)
DB_USER = os.getenv("SUPABASE_USER")
DB_PASSWORD = os.getenv("SUPABASE_PASSWORD") 
DB_HOST = os.getenv("SUPABASE_HOST")
DB_NAME = os.getenv("SUPABASE_DBNAME", "postgres")

# Use DATABASE_URL if provided, otherwise construct direct connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL and all([DB_USER, DB_PASSWORD, DB_HOST]):
    # Create URL using SQLAlchemy's URL.create for proper SSL handling
    database_url = URL.create(
        "postgresql+asyncpg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=5432,                # Direct connection port (not pgbouncer 6543)
        database=DB_NAME,
        query={"ssl": "true"},    # asyncpg SSL configuration
    )
    DATABASE_URL = str(database_url)

if not DATABASE_URL:
    raise ValueError("Database connection URL is not set. Please set DATABASE_URL or individual SUPABASE_* variables.")

# Optimized engine configuration for direct Supabase connection
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,            # Tune for your process count
    max_overflow=10,        # Additional connections during peaks
    pool_pre_ping=True,     # Health check connections
    pool_recycle=1800,      # 30 min recycle
    pool_timeout=30,        # Connection acquisition timeout
    execution_options={
        "compiled_cache": {},
    },
    connect_args={
        # RE-ENABLE prepared statement cache (safe with direct connection)
        "statement_cache_size": 1000,
        "command_timeout": 30,
        "server_settings": {
            "application_name": "maqro_backend_direct",
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