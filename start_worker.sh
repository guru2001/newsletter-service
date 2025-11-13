#!/bin/bash
# Start Celery worker for newsletter service

echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info

