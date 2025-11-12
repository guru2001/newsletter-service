from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class Topic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None

class TopicSubscriber(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    topic_id: int
    created_at: datetime

class Content(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_id: int
    content_text: str
    scheduled_time: datetime
    created_at: datetime