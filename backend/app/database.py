from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextvars import ContextVar
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/verishield")

# Tenant context variable
tenant_id: ContextVar[str] = ContextVar('tenant_id', default='public')

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session with tenant context."""
    db = SessionLocal()
    try:
        # Set search path to tenant schema
        current_tenant = tenant_id.get()
        if current_tenant and current_tenant != 'public':
            db.execute(f"SET search_path TO tenant_{current_tenant}, public")
        yield db
    finally:
        db.close()

def create_tenant_schema(tenant_id: str):
    """Create a new schema for a tenant."""
    with engine.connect() as conn:
        # Create schema if it doesn't exist
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS tenant_{tenant_id}")
        conn.commit()

        # Grant permissions
        conn.execute(f"GRANT USAGE ON SCHEMA tenant_{tenant_id} TO verishield_user")
        conn.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tenant_{tenant_id} TO verishield_user")
        conn.commit()

def get_tenant_schema(tenant_id: str) -> MetaData:
    """Get metadata for a specific tenant schema."""
    schema_name = f"tenant_{tenant_id}" if tenant_id != 'public' else 'public'
    return MetaData(schema=schema_name)

# Initialize public schema tables
def init_db():
    """Initialize database with base tables."""
    Base.metadata.create_all(bind=engine)