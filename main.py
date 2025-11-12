from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

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

app = FastAPI(title="Newsletter Service", version="0.1.0")


# Topic Endpoints
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


# Content Endpoints
@app.post("/content", response_model=ContentSchema, status_code=status.HTTP_201_CREATED)
def create_content(content: ContentCreate, db: Session = Depends(get_db)):
    """Create new newsletter content."""
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {content.topic_id} not found"
        )
    
    db_content = Content(
        topic_id=content.topic_id,
        content_text=content.content_text,
        scheduled_time=content.scheduled_time
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to Newsletter Service API", "docs": "/docs"}
