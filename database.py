from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DB_URL

# Add connection timeout and pool settings to prevent hanging
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
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

