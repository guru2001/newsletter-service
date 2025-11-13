#!/bin/bash
# Start both FastAPI server and Celery worker

echo "Initializing database tables..."
python3 setup_db.py

echo "Starting FastAPI server..."
# Use single worker to reduce memory usage
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 &

echo "Starting Celery worker..."
# Use solo pool (single process) instead of prefork to save memory
# This is less efficient but uses much less memory
celery -A celery_app worker --loglevel=info --pool=solo --concurrency=1

