# Newsletter Service

A newsletter service that automatically sends scheduled content to subscribers based on topics. Built with FastAPI, Celery, PostgreSQL, and SendGrid. Deployed on render

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
│  Creation   │  ← Service for Creating Content
│  Service    │
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
│  Sending    │  ← Email Delivery Service
│  Service    │
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
    "scheduled_time_utc": "2025-11-13T10:00:00Z"
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
# replace email ids
curl -X POST "https://newsletter-service-g3km.onrender.com/topics/1/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"emails": ["alice@example.com", "bob@example.com"]}'

# 3. Schedule content (replace topic_id and scheduled_time_utc)
curl -X POST "https://newsletter-service-g3km.onrender.com/content" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "content_text": "<h1>This Week News</h1><p>Content here...</p>",
    "scheduled_time_utc": "2025-11-13T10:02:00Z"
  }'
```

**Interactive API Documentation:** https://newsletter-service-g3km.onrender.com/docs

---

### Free Tier Limitations

**⚠️ Important:** Render's free tier has the following limitations:

- **Spin-down on Inactivity:** Free instances automatically spin down after 15 minutes of inactivity
- **Cold Start Delay:** First request after spin-down can take 50+ seconds to wake up the service
- **Impact on Scheduled Tasks:** Celery worker also spins down, but scheduled tasks will execute when the service wakes up (may be delayed)

**Note:** The service will automatically wake up when receiving requests, but users should expect initial delays after periods of inactivity.

---

### ⚠️ Known Limitations & Areas for Improvement

#### 1. **Lack of Email Retry Logic**
- If an email fails to send due to network or provider errors, it will not be retried.
- No built-in mechanism to automatically recover from transient failures.

#### 2. **No Outbound Email Rate Limiting**
- High volume scenarios may lead to exceeding provider (e.g., SendGrid) rate limits.
- Could result in dropped or delayed emails if many users subscribe at once.

#### 3. **Missing Unsubscribe & Content Editing Functionality**
- Users currently cannot unsubscribe or update their subscription via API.
- Editing existing newsletter content is not possible through the API.

#### 4. **Manual UTC Timezone Handling**
- All scheduling is done in UTC; users must convert their local time.
- No automatic timezone detection or conversion in the API.

### Improvements in Design and Scalability

To further enhance the robustness, efficiency, and scalability of the newsletter service, the following architectural improvements are recommended:

1. **Rate Limiting**
   - Implement outbound email rate limits (with Celery, Redis, etc.) to prevent exceeding provider quotas and to guard against traffic spikes.

2. **Parallel Email Sending**
   - Deliver emails using Celery concurrency or async batch sending, distributing recipients among workers to improve speed and throughput.

3. **Database Scalability and Query Optimization**
   - Leverage database read replicas for heavy read endpoints, add indexes to common fields, and optimize queries for performance.

4. **Add Logging**
   - Implement structured logging to monitor task execution, errors, and performance issues.

These improvements, when implemented together, significantly increase reliability, handle increased usage, and enable robust scaling for much larger subscriber bases and higher sending frequencies.

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SendGrid API Docs](https://docs.sendgrid.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)