#!/bin/bash
# Start both FastAPI server and Celery worker
uvicorn main:app --host 0.0.0.0 --port $PORT &
celery -A celery_app worker --loglevel=info

