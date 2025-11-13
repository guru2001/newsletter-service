from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DB_URL

# Add connection timeout and pool settings to prevent hanging and memory leaks
# Limit pool size to prevent memory issues on free tier
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,  # Limit pool size to 5 connections
    max_overflow=10,  # Allow up to 10 overflow connections
    pool_timeout=30,  # Timeout when getting connection from pool
    connect_args={"connect_timeout": 10} if "postgresql" in DB_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

