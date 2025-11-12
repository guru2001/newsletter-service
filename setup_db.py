#!/usr/bin/env python3
"""Script to create the database and apply the schema."""

import os
import sys
from urllib.parse import urlparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import DB_URL

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

    # Apply schema
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Execute each statement, ignore "already exists" errors
    for statement in schema_sql.split(';'):
        statement = statement.strip()
        if not statement:
            continue
        try:
            cursor.execute(statement)
            conn.commit()
        except psycopg2.Error as e:
            if "already exists" in str(e).lower():
                conn.rollback()
            else:
                raise
    
    print("Schema applied successfully!")
    cursor.close()
    conn.close()

except psycopg2.OperationalError as e:
    print(f"Error: {e}")
    print(f"Check your DATABASE_URL: {db_url}")
    sys.exit(1)
except FileNotFoundError:
    print("Error: schema.sql not found!")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
