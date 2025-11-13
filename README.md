# Newsletter Service

A production-ready newsletter service that automatically sends scheduled content to subscribers based on topics. Built with FastAPI, Celery, PostgreSQL, and SendGrid.

**🚀 Live Deployment:** https://newsletter-service-g3km.onrender.com  
**📚 Interactive API Docs:** https://newsletter-service-g3km.onrender.com/docs

---

## Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Improvements & Pitfalls](#-improvements--pitfalls)
- [Development Journey](#-development-journey)

---

## 🎯 Features

- ✅ **Topic-based Content Management**: Organize newsletters by topics
- ✅ **Subscriber Management**: Subscribe users to specific topics (bulk support)
- ✅ **Scheduled Delivery**: Schedule content to be sent at specific times
- ✅ **Automatic Email Sending**: Celery task queue handles scheduled deliveries
- ✅ **RESTful API**: Complete REST API with OpenAPI documentation
- ✅ **Production Ready**: Deployed on Render with PostgreSQL and Redis

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI (Python) | REST API with automatic OpenAPI docs |
| **Task Queue** | Celery | Scheduled task execution |
| **Message Broker** | Redis | Task queue backend |
| **Database** | PostgreSQL | Persistent data storage |
| **Email Service** | SendGrid API | Email delivery (free tier: 100/day) |
| **ORM** | SQLAlchemy | Database abstraction |

### System Flow

```
┌─────────────┐
│   FastAPI   │  ← REST API Endpoints
│   Server    │
└──────┬──────┘
       │
       ├─── Creates Content → Schedules Celery Task
       │
┌──────▼──────┐
│   Celery    │  ← Task Queue (Redis)
│   Worker    │
└──────┬──────┘
       │
       ├─── Executes at Scheduled Time
       │
┌──────▼──────┐
│  SendGrid   │  ← Email Delivery
│     API     │
└─────────────┘
```

### Database Schema

**Topics Table**
- `id` (Primary Key)
- `name` (Unique)
- `description` (Text)

**Topic Subscribers Table**
- `id` (Primary Key)
- `email` (Indexed)
- `topic_id` (Foreign Key)
- `created_at` (Timestamp)
- Unique constraint: (`email`, `topic_id`)

**Content Table**
- `id` (Primary Key)
- `topic_id` (Foreign Key)
- `content_text` (HTML)
- `scheduled_time_utc` (Timestamp)
- `delivered` (Boolean)
- `created_at` (Timestamp)

---

## 📖 API Documentation

**Base URL:** `https://newsletter-service-g3km.onrender.com`

### 1. List Topics

```bash
curl https://newsletter-service-g3km.onrender.com/topics
```

### 2. Create Topic

```bash
curl -X POST "https://newsletter-service-g3km.onrender.com/topics" \
  -H "Content-Type: application/json" \
  -d '{"name": "Technology", "description": "Latest tech news and updates"}'
```

### 3. Subscribe Emails to Topic

```bash
curl -X POST "https://newsletter-service-g3km.onrender.com/topics/1/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"emails": ["user1@example.com", "user2@example.com"]}'
```

**Note:** Supports bulk subscription. Replace `1` with your topic ID.

### 4. Get Topic Subscribers

```bash
curl https://newsletter-service-g3km.onrender.com/topics/1/subscribers
```

### 5. Schedule Newsletter Content

```bash
curl -X POST "https://newsletter-service-g3km.onrender.com/content" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "content_text": "<h1>Welcome!</h1><p>Newsletter content...</p>",
    "scheduled_time_utc": "2024-01-15T10:00:00Z"
  }'
```

**Important:** `scheduled_time_utc` must be in UTC, in the future, and ISO 8601 format.

### Complete Example Workflow

```bash
# 1. Create a topic
curl -X POST "https://newsletter-service-g3km.onrender.com/topics" \
  -H "Content-Type: application/json" \
  -d '{"name": "Weekly Digest", "description": "Weekly news"}'

# 2. Subscribe users (replace topic_id from step 1 response)
curl -X POST "https://newsletter-service-g3km.onrender.com/topics/1/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"emails": ["alice@example.com", "bob@example.com"]}'

# 3. Schedule content (replace topic_id and scheduled_time_utc)
curl -X POST "https://newsletter-service-g3km.onrender.com/content" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "content_text": "<h1>This Week News</h1><p>Content here...</p>",
    "scheduled_time_utc": "2024-01-15T10:02:00Z"
  }'
```

**Interactive API Documentation:** https://newsletter-service-g3km.onrender.com/docs

---

## 🌐 Deployment

**Service URL:** https://newsletter-service-g3km.onrender.com  
**API Docs:** https://newsletter-service-g3km.onrender.com/docs

### Deploying to Render

1. **Create PostgreSQL Database**
   - Render Dashboard → New → PostgreSQL
   - Copy the Internal Database URL

2. **Create Redis Instance**
   - Render Dashboard → New → Key Value Instance (Redis)
   - Copy the Internal Redis URL

3. **Create Web Service**
   - Connect GitHub repository
   - Set Build Command: `pip install -r requirements.txt`
   - Set Start Command: `bash start.sh`
   - Add environment variables:
     ```
     DATABASE_URL=<postgres-url>
     CELERY_BROKER_URL=<redis-url>
     CELERY_RESULT_BACKEND=rpc://
     SENDGRID_API_KEY=<your-api-key>
     SENDGRID_FROM_EMAIL=<verified-email>
     ```

4. **SendGrid Setup**
   - Sign up at [sendgrid.com](https://sendgrid.com)
   - Create API key with "Mail Send" permissions
   - Verify sender email in Settings → Sender Authentication

---

## 🔍 Improvements & Pitfalls

### Known Limitations

#### 1. **No Email Retry Mechanism**
**Current Behavior:**
```python
# In tasks.py - if SendGrid fails, email is lost
response = sg.send(message)
if response.status_code not in [200, 202]:
    error_count += 1
    # No retry - email is lost
```

**Impact:** 
- Temporary SendGrid outages result in lost emails
- Network hiccups cause permanent failures
- No automatic recovery mechanism

**Solution Example:**
```python
from celery import Task
from celery.retry import Retry

@celery_app.task(bind=True, max_retries=3)
def send_newsletter(self, content_id):
    try:
        response = sg.send(message)
        if response.status_code not in [200, 202]:
            raise Exception("SendGrid error")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### 2. **No Delivery Tracking**
**Current Behavior:**
- Only knows if task executed, not if email was delivered
- Cannot detect bounces, spam reports, or unsubscribes

**Impact:**
- Sending to invalid emails wastes quota
- No engagement metrics (opens, clicks)
- Compliance issues (must handle bounces)

**Solution Example:**
```python
# Add webhook endpoint
@app.post("/webhooks/sendgrid")
def sendgrid_webhook(events: List[dict]):
    for event in events:
        if event['event'] == 'bounce':
            # Mark email as invalid
            unsubscribe_email(event['email'])
        elif event['event'] == 'open':
            # Track engagement
            log_email_open(event['email'])
```

#### 3. **No Rate Limiting**
**Current Behavior:**
```python
# main.py - no rate limiting
@app.post("/content")
def create_content(content: ContentCreate):
    # Anyone can spam the API
    pass
```

**Impact:**
- Malicious users can send thousands of emails
- Free tier quota exhausted quickly
- Service abuse potential

**Solution Example:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/content")
@limiter.limit("10/minute")
def create_content(content: ContentCreate):
    pass
```

#### 4. **No Authentication**
**Current Behavior:**
- All endpoints are publicly accessible
- Anyone can create topics, subscribe emails, schedule content

**Impact:**
- Security vulnerability
- Unauthorized content creation
- Potential spam abuse

**Solution Example:**
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
    return api_key

@app.post("/content")
def create_content(content: ContentCreate, api_key: str = Depends(verify_api_key)):
    pass
```

#### 5. **No Unsubscribe Mechanism**
**Current Behavior:**
- Users cannot unsubscribe themselves
- Must manually remove from database

**Impact:**
- GDPR/CAN-SPAM compliance violations
- Legal liability
- Poor user experience

**Solution Example:**
```python
@app.get("/unsubscribe/{token}")
def unsubscribe(token: str):
    # Verify token and unsubscribe
    subscriber = verify_unsubscribe_token(token)
    db.delete(subscriber)
    return {"message": "Unsubscribed successfully"}

# In email template:
# <a href="https://service.com/unsubscribe/{{token}}">Unsubscribe</a>
```

#### 6. **Limited Timezone Support**
**Current Behavior:**
```python
# Must always provide UTC
scheduled_time_utc: datetime  # User must convert themselves
```

**Impact:**
- User confusion (what time is 10:00 UTC in my timezone?)
- Scheduling errors
- Poor UX

**Solution Example:**
```python
from datetime import timezone
import pytz

class ContentCreate(BaseModel):
    scheduled_time: datetime
    timezone: str = "UTC"  # e.g., "America/New_York"
    
    def to_utc(self):
        tz = pytz.timezone(self.timezone)
        return self.scheduled_time.replace(tzinfo=tz).astimezone(timezone.utc)
```

#### 7. **No Content Editing**
**Current Behavior:**
- Once content is created, it cannot be modified
- Must delete and recreate (loses scheduling)

**Impact:**
- Typos require full recreation
- Cannot update content before sending
- Poor content management

**Solution Example:**
```python
@app.put("/content/{content_id}")
def update_content(content_id: int, updates: ContentUpdate):
    content = db.query(Content).filter(Content.id == content_id).first()
    if content.delivered:
        raise HTTPException(400, "Cannot edit delivered content")
    # Update content
    content.content_text = updates.content_text
    db.commit()
```

#### 8. **Sequential Email Sending**
**Current Behavior:**
```python
# Sends one by one - slow for 1000 subscribers
for subscriber in subscribers:
    sg.send(message)  # Waits for each
```

**Impact:**
- 1000 emails = 1000 API calls = ~5 minutes
- Slow delivery
- Higher API rate limit risk

**Solution Example:**
```python
# Use SendGrid batch API
messages = [
    Mail(from_email=FROM, to_emails=sub.email, ...)
    for sub in subscribers
]
sg.client.mail.send.post(request_body={"personalizations": messages})
# Single API call for all emails
```

#### 9. **No Monitoring**
**Current Behavior:**
```python
print(f"Email sent to {email}")  # Only console logs
```

**Impact:**
- Cannot track success rates
- No alerting on failures
- Difficult to debug production issues

**Solution Example:**
```python
import logging
from prometheus_client import Counter

email_sent = Counter('emails_sent_total', 'Total emails sent')
email_failed = Counter('emails_failed_total', 'Total emails failed')

logger = logging.getLogger(__name__)
logger.info("Email sent", extra={"email": email, "status": "success"})
email_sent.inc()
```

#### 10. **Single Worker on Free Tier**
**Current Behavior:**
```bash
# start.sh - both in same process
uvicorn main:app &  # Background
celery worker        # Foreground
```

**Impact:**
- Web server restart kills worker
- No independent scaling
- Memory constraints

**Solution:**
- Separate Render services (paid tier)
- Or use separate worker service on different platform

---

## 🛠️ Development Journey

### Technical Decisions

**Why FastAPI?**
```python
# Automatic OpenAPI docs - no manual documentation needed
@app.post("/content", response_model=ContentSchema)
def create_content(content: ContentCreate):
    # Type safety with Pydantic validation
    # Async support for better performance
    pass
```
- Modern async support for high concurrency
- Automatic OpenAPI/Swagger documentation
- Type safety with Pydantic models
- Excellent performance (comparable to Node.js)

**Why Celery?**
```python
# Scheduled tasks with eta parameter
send_newsletter.apply_async(
    args=[content_id],
    eta=scheduled_time_utc  # Execute at specific time
)
```
- Industry-standard task queue for Python
- Built-in support for scheduled tasks (`eta` parameter)
- Task persistence via Redis (survives restarts)
- Horizontal scaling (add more workers easily)

**Why SendGrid API over SMTP?**
```python
# REST API - no port restrictions
sg = SendGridAPIClient(api_key)
response = sg.send(message)  # Works on any platform
```
- Render free tier blocks SMTP ports (25, 465, 587)
- REST-based, works from any cloud platform
- Better error handling and status codes
- Free tier: 100 emails/day (sufficient for testing)

### Challenges & Solutions

#### Challenge 1: Scheduled Task Persistence

**Problem:** 
- Service restarts lose in-memory scheduled tasks
- How to ensure emails are sent even after deployment?

**Initial Attempt:**
```python
# ❌ This doesn't work - lost on restart
import schedule
schedule.every().day.at("10:00").do(send_email)
```

**Solution:**
```python
# ✅ Tasks stored in Redis (persistent)
task_result = send_newsletter.apply_async(
    args=[content_id],
    eta=scheduled_time_utc  # Stored in Redis
)
# Even if service restarts, Celery worker picks up from Redis
```

**Key Configuration:**
```python
# celery_app.py
task_acks_late=True  # Only acknowledge after completion
broker_connection_retry=True  # Reconnect if Redis goes down
```

#### Challenge 2: Free Tier Deployment Constraints

**Problem:** 
- Render free tier blocks outbound SMTP ports
- Traditional email sending impossible

**Discovery:**
```bash
# ❌ This fails on Render free tier
smtp = smtplib.SMTP('smtp.gmail.com', 587)  
# Error: Connection refused (port blocked)
```

**Solution:**
```python
# ✅ SendGrid API - REST-based, no ports needed
from sendgrid import SendGridAPIClient
sg = SendGridAPIClient(api_key)
response = sg.send(message)  # HTTP request, works anywhere
```

**Trade-off:**
- Requires SendGrid account (but free tier available)
- More reliable than SMTP for cloud deployments

#### Challenge 3: Running Multiple Services on Free Tier

**Problem:**
- Render free tier: one service instance
- Need both FastAPI (web) and Celery (worker)
- Separate services require paid tier

**Solution:**
```bash
# start.sh - run both in same process
uvicorn main:app --host 0.0.0.0 --port $PORT &  # Background
celery -A celery_app worker --pool=solo          # Foreground
```

**Trade-offs:**
- ✅ Works on free tier
- ❌ Worker affected by web server restarts
- ❌ Cannot scale independently
- ✅ Sufficient for demonstration purposes

#### Challenge 4: Database Initialization

**Problem:**
- First deployment: tables don't exist
- Manual setup is error-prone

**Solution:**
```python
# setup_db.py - auto-creates tables
Base.metadata.create_all(bind=engine)

# Integrated into start.sh
python3 setup_db.py  # Runs before services start
```

**Benefits:**
- Idempotent (safe to run multiple times)
- No manual database setup required
- Works on every deployment

#### Challenge 5: Timezone Handling

**Problem:**
- Users in different timezones
- Confusion: "When is 10:00 UTC in my time?"

**Initial Confusion:**
```python
# User provides: "2024-01-15 10:00" - what timezone?
scheduled_time = datetime(2024, 1, 15, 10, 0)  # Naive datetime
```

**Solution:**
```python
# Enforce UTC, validate timezone-aware
if scheduled_time_utc.tzinfo is None:
    scheduled_time_utc = scheduled_time_utc.replace(tzinfo=timezone.utc)

# Reject past times
if scheduled_time_utc <= datetime.now(timezone.utc):
    raise HTTPException(400, "Time must be in future")
```

**Future Improvement:**
- Accept user timezone, convert to UTC internally
- Display times in user's timezone in API responses

#### Challenge 6: Error Handling & Reliability

**Problem:**
- What if SendGrid is down?
- What if network fails?
- How to prevent duplicate sends?

**Solution:**
```python
# Mark as delivered to prevent retries
content.delivered = True
db.commit()

# Log all errors for debugging
try:
    response = sg.send(message)
except Exception as e:
    logger.error(f"Failed to send: {e}")
    error_count += 1
    # Continue with other emails
```

**Current Limitation:**
- No automatic retry (emails may be lost)
- Future: Implement exponential backoff retry

**Example of Better Error Handling:**
```python
# Future improvement
@celery_app.task(bind=True, max_retries=3)
def send_newsletter(self, content_id):
    try:
        sg.send(message)
    except Exception as exc:
        # Retry with exponential backoff: 2s, 4s, 8s
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SendGrid API Docs](https://docs.sendgrid.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

## 📄 License

This project is provided as-is for demonstration purposes.

---

## 📧 Submission Details

**Repository:** [GitHub Repository URL]  
**Deployment:** https://newsletter-service-g3km.onrender.com  
**API Documentation:** https://newsletter-service-g3km.onrender.com/docs

**Requirements Met:**
- ✅ Subscriber email management via API
- ✅ Content creation with scheduling via API
- ✅ Topic-based content segregation and subscriptions
- ✅ Automatic email sending at scheduled times
- ✅ Free email service (SendGrid) on free deployment (Render)
- ✅ Comprehensive documentation with improvements, pitfalls, and development journey

---

**Note:** This service is designed for demonstration purposes. For production use, implement the improvements listed above, especially authentication, retry mechanisms, and monitoring.
