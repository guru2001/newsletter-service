import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://guru@localhost:5432/newsletter_system")
