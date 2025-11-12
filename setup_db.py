#!/usr/bin/env python3
"""Script to create the database and apply the schema using SQLAlchemy models."""

import os
import sys
from urllib.parse import urlparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine

from config import DB_URL
from models import Base

# Get database URL
db_url = os.getenv("DATABASE_URL", DB_URL)
parsed = urlparse(db_url)
db_name = parsed.path.lstrip('/')

# Build admin URL (connect to postgres db to create target db)
if parsed.password:
    admin_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname or 'localhost'}:{parsed.port or 5432}/postgres"
else:
    admin_url = f"postgresql://{parsed.username}@{parsed.hostname or 'localhost'}:{parsed.port or 5432}/postgres"

try:
    # Create database if it doesn't exist
    conn = psycopg2.connect(admin_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    if not cursor.fetchone():
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        print(f"Created database '{db_name}'")
    cursor.close()
    conn.close()

    # Create tables using SQLAlchemy models
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    print("Schema applied successfully using SQLAlchemy models!")
    engine.dispose()

except psycopg2.OperationalError as e:
    print(f"Error: {e}")
    print(f"Check your DATABASE_URL: {db_url}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
