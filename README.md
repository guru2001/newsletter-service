# Newsletter Service

A robust newsletter service built with FastAPI, Celery, and PostgreSQL that allows you to send scheduled newsletters to subscribers based on topics.

## 🎯 Features

- ✅ **Topic Management**: Create and manage multiple newsletter topics
- ✅ **Subscriber Management**: Subscribe/unsubscribe emails to specific topics (bulk support)
- ✅ **Content Scheduling**: Create newsletter content with scheduled send times
- ✅ **Automatic Email Delivery**: Celery-based task queue automatically sends emails at scheduled times
- ✅ **SMTP Integration**: Send emails via any SMTP service (Gmail, SendGrid, etc.)
- ✅ **RESTful API**: Clean, well-documented API endpoints
- ✅ **Database Schema**: PostgreSQL with proper relationships and constraints

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with RabbitMQ broker
- **Email**: SMTP (smtplib)
- **Validation**: Pydantic
- **Package Management**: uv

## 📋 Requirements

- Python 3.12+
- PostgreSQL
- RabbitMQ
- SMTP account (Gmail, SendGrid, etc.)

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd newsletter_service
```

### 2. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/newsletter_system

# Celery (RabbitMQ)
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=rpc://

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true
```

**Note**: For Gmail, you'll need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### 4. Setup Database

```bash
python3 setup_db.py
```

This script will:
- Create the database if it doesn't exist
- Create all necessary tables (topics, topic_subscribers, content)

### 5. Start Services

You need to run **3 services** in separate terminals:

#### Terminal 1: FastAPI Server
```bash
uvicorn main:app --reload
```
Server will be available at: http://localhost:8000
Interactive API docs at: http://localhost:8000/docs

#### Terminal 2: Celery Worker
```bash
celery -A celery_app worker --loglevel=info
```
Or use the provided script:
```bash
./start_worker.sh
```

#### Terminal 3: (Optional) RabbitMQ
If RabbitMQ is not running as a service:
```bash
rabbitmq-server
```

## 📡 API Endpoints

### Topics

#### List All Topics
```bash
GET /topics
```

#### Create Topic
```bash
POST /topics
Content-Type: application/json

{
  "name": "Technology",
  "description": "Latest tech news and updates"
}
```

### Subscriptions

#### Subscribe Emails to Topic
```bash
POST /topics/{topic_id}/subscribe
Content-Type: application/json

{
  "emails": ["user1@example.com", "user2@example.com"]
}
```

#### Get Subscribers for Topic
```bash
GET /topics/{topic_id}/subscribers
```

### Content

#### Create Newsletter Content
```bash
POST /content
Content-Type: application/json

{
  "topic_id": 1,
  "content_text": "Welcome to our newsletter! This is the content...",
  "scheduled_time_utc": "2025-01-15T10:00:00Z"
}
```

**Note**: `scheduled_time_utc` must be in the future and in ISO 8601 format with timezone.

## 📖 Usage Examples

### Complete Workflow

1. **Create a Topic**
```bash
curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Technology",
    "description": "Tech news and updates"
  }'
```

2. **Subscribe Emails**
```bash
curl -X POST "http://localhost:8000/topics/1/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["user@example.com", "another@example.com"]
  }'
```

3. **Create Scheduled Content**
```bash
curl -X POST "http://localhost:8000/content" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "content_text": "This is your newsletter content!",
    "scheduled_time_utc": "2025-01-15T10:00:00Z"
  }'
```

4. **The Celery worker will automatically send the newsletter at the scheduled time!**

### Using the Interactive API Docs

Visit http://localhost:8000/docs for an interactive Swagger UI where you can test all endpoints directly.

## 🗄️ Database Schema

```
topics
├── id (PK)
├── name (UNIQUE)
└── description

topic_subscribers
├── id (PK)
├── email
├── topic_id (FK -> topics.id)
└── created_at

content
├── id (PK)
├── topic_id (FK -> topics.id)
├── content_text
├── scheduled_time_utc
└── created_at
```

## 🚢 Deployment

### Option 1: Heroku

1. Create a `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: celery -A celery_app worker --loglevel=info
```

2. Add Heroku addons:
```bash
heroku addons:create heroku-postgresql
heroku addons:create cloudamqp
```

3. Deploy:
```bash
git push heroku main
```

### Option 2: Railway

1. Connect your GitHub repo to Railway
2. Add PostgreSQL and RabbitMQ services
3. Set environment variables
4. Deploy

### Option 3: Docker (Recommended for Production)

Create a `Dockerfile` and `docker-compose.yml` for easy deployment.

## ✅ Assignment Requirements Checklist

- ✅ System to enter subscriber's email ids
- ✅ System to enter content with time & content text
- ✅ Content segregated on topic basis
- ✅ Users subscribe to specific topics
- ✅ Automatic sending at specified times (Celery)
- ✅ Email delivery via SMTP
- ✅ RESTful API endpoints
- ✅ Documentation

## 🔍 Improvements and Pitfalls

### Improvements Made

1. **Bulk Subscription Support**: The API supports subscribing multiple emails at once
2. **Error Handling**: Comprehensive error handling with proper HTTP status codes
3. **Timezone Support**: Proper UTC timezone handling for scheduled times
4. **Validation**: Input validation using Pydantic schemas
5. **Graceful Degradation**: Content creation succeeds even if Celery is temporarily unavailable
6. **Database Constraints**: Unique constraints prevent duplicate subscriptions
7. **API Documentation**: Auto-generated OpenAPI/Swagger documentation

### Known Limitations & Pitfalls

1. **No Frontend**: As per requirements, no frontend is provided. All operations are via API
2. **SMTP Rate Limits**: Free SMTP services (like Gmail) have rate limits. For production, consider:
   - Using a dedicated email service (SendGrid, Mailgun, AWS SES)
   - Implementing email queuing with retry logic
   - Rate limiting and batching

3. **No Email Templates**: Currently sends plain text emails. Could be improved with:
   - HTML email templates
   - Email personalization
   - Unsubscribe links

4. **No Authentication**: API endpoints are unprotected. For production:
   - Add API key authentication
   - Implement user roles and permissions
   - Add rate limiting

5. **Single Worker**: Currently runs a single Celery worker. For scale:
   - Run multiple workers
   - Use Celery beat for recurring tasks
   - Implement task prioritization

6. **No Monitoring**: Missing observability:
   - Task success/failure tracking
   - Email delivery status
   - Performance metrics
   - Logging aggregation

7. **Database Migrations**: Using SQLAlchemy's `create_all()` instead of proper migrations (Alembic)

8. **No Retry Logic**: Failed email sends are not retried automatically

9. **No Unsubscribe Feature**: Subscribers cannot unsubscribe via email link

10. **Timezone Handling**: Currently assumes all times are UTC. Could add timezone preferences per user

### Future Enhancements

- [ ] Email templates with HTML support
- [ ] Unsubscribe functionality
- [ ] Email delivery tracking
- [ ] Task retry mechanism
- [ ] API authentication
- [ ] Database migrations (Alembic)
- [ ] Monitoring and logging (Prometheus, Grafana)
- [ ] Rate limiting
- [ ] Webhook support for delivery status
- [ ] User timezone preferences
- [ ] Recurring newsletter support

## 🧪 Testing

### Manual Testing

1. Start all services (FastAPI, Celery, RabbitMQ)
2. Use the interactive API docs at `/docs`
3. Create a topic, subscribe emails, create content
4. Verify emails are sent at scheduled time

### Example Test Flow

```bash
# 1. Create topic
curl -X POST "http://localhost:8000/topics" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Topic", "description": "Test"}'

# 2. Subscribe
curl -X POST "http://localhost:8000/topics/1/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"emails": ["your-email@example.com"]}'

# 3. Create content (5 minutes from now)
curl -X POST "http://localhost:8000/content" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "content_text": "Test newsletter",
    "scheduled_time_utc": "'$(date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
```

## 📝 Commit History

This project follows good Git practices with meaningful commit messages documenting the development process.

## 📄 License

This project is created as an assignment submission.

## 👤 Author

[Your Name]

## 🙏 Acknowledgments

- FastAPI documentation
- Celery documentation
- Stack Overflow community for various code snippets (cited in code comments where applicable)

---

**Note**: This service is designed for the assignment requirements. For production use, additional security, monitoring, and scalability features should be implemented.

