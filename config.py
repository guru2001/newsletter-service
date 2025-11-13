import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://guru@localhost:5432/newsletter_system")
# Using RabbitMQ as broker
# Default: amqp://guest:guest@localhost:5672//
# Format: amqp://username:password@host:port/vhost
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

# Email configuration (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "guru.ravi22x@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "yvmj sruw bdfk dmmo")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
