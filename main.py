from fastapi import FastAPI, Depends, HTTPException, status
import traceback
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from database import get_db
from models import Topic, TopicSubscriber, Content
from schemas import (
    Topic as TopicSchema,
    TopicCreate,
    TopicSubscriber as TopicSubscriberSchema,
    BulkSubscribeRequest,
    Content as ContentSchema,
    ContentCreate,
)
from tasks import send_newsletter

app = FastAPI(title="Newsletter Service", version="0.1.0")


# Topic Endpoints
@app.get("/topics", response_model=List[TopicSchema])
def list_topics(db: Session = Depends(get_db)):
    """List all topics with their IDs."""
    topics = db.query(Topic).all()
    return topics


@app.post("/topics", response_model=TopicSchema, status_code=status.HTTP_201_CREATED)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    """Create a new topic."""
    # Check if topic with same name already exists
    existing = db.query(Topic).filter(Topic.name == topic.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic with name '{topic.name}' already exists"
        )
    
    db_topic = Topic(name=topic.name, description=topic.description)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


# Subscriber Endpoints
@app.post("/topics/{topic_id}/subscribe", response_model=List[TopicSubscriberSchema], status_code=status.HTTP_201_CREATED)
def subscribe_to_topic(topic_id: int, subscribe: BulkSubscribeRequest, db: Session = Depends(get_db)):
    """Subscribe one or more emails to a topic (bulk support)."""
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )
    
    created_subscribers = []
    
    for email in subscribe.emails:
        # Check if already subscribed
        existing = db.query(TopicSubscriber).filter(
            TopicSubscriber.topic_id == topic_id,
            TopicSubscriber.email == email
        ).first()
        
        if existing:
            continue  # Skip already subscribed emails
        
        subscriber = TopicSubscriber(email=email, topic_id=topic_id)
        db.add(subscriber)
        created_subscribers.append(subscriber)
    
    db.commit()
    
    # Refresh all created subscribers
    for subscriber in created_subscribers:
        db.refresh(subscriber)
    
    return created_subscribers


@app.get("/topics/{topic_id}/subscribers", response_model=List[TopicSubscriberSchema])
def get_topic_subscribers(topic_id: int, db: Session = Depends(get_db)):
    """Get all subscribers for a specific topic."""
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )
    
    subscribers = db.query(TopicSubscriber).filter(TopicSubscriber.topic_id == topic_id).all()
    return subscribers


# Content Endpoints
@app.post("/content", response_model=ContentSchema, status_code=status.HTTP_201_CREATED)
def create_content(content: ContentCreate, db: Session = Depends(get_db)):
    """Create new newsletter content and trigger Celery task to send newsletter."""
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {content.topic_id} not found"
        )
    
    # Validate scheduled_time_utc must be in the future
    now = datetime.now(timezone.utc)
    scheduled_time_utc = content.scheduled_time_utc
    
    # If scheduled_time_utc is timezone-naive, assume UTC
    if scheduled_time_utc.tzinfo is None:
        scheduled_time_utc = scheduled_time_utc.replace(tzinfo=timezone.utc)
    
    # Reject if scheduled_time_utc is not in the future
    if scheduled_time_utc <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scheduled time must be in the future. Provided: {scheduled_time_utc}, Current: {now}"
        )
    
    db_content = Content(
        topic_id=content.topic_id,
        content_text=content.content_text,
        scheduled_time_utc=content.scheduled_time_utc
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    
    # Schedule Celery task to run at the scheduled time
    # Wrap in try-except to prevent content creation from failing if Celery has issues
    try:
        print(f"Scheduling newsletter to send at {scheduled_time_utc}")
        task_result = send_newsletter.apply_async(args=[db_content.id], eta=scheduled_time_utc)
        print(f"Newsletter scheduled to send at {scheduled_time_utc}, task_id: {task_result.id if task_result else 'N/A'}")
    except Exception as e:
        # Log error but don't fail the request if Celery fails
        print(f"Warning: Failed to schedule Celery task: {e}")
        traceback.print_exc()
        # Don't raise - allow content creation to succeed even if scheduling fails
    
    return db_content


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to Newsletter Service API", "docs": "/docs"}
