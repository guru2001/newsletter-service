from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# Topic Schemas
class Topic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None

class TopicCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Subscriber Schemas
class TopicSubscriber(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    topic_id: int
    created_at: datetime

class BulkSubscribeRequest(BaseModel):
    emails: list[EmailStr]

# Content Schemas
class Content(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_id: int
    content_text: str
    scheduled_time_utc: datetime
    delivered: bool
    created_at: datetime

class ContentCreate(BaseModel):
    topic_id: int
    content_text: str
    scheduled_time_utc: datetime