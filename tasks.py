from celery_app import celery_app
from database import SessionLocal
from models import Content, TopicSubscriber, Topic
from config import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import traceback


@celery_app.task(name="tasks.send_newsletter")
def send_newsletter(content_id: int):
    """
    Celery task to send newsletter emails to all subscribers of a topic.
    
    Args:
        content_id: The ID of the Content record to send
    """
    db = None
    try:
        db = SessionLocal()
        # Get the content
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            print(f"Error: Content with id {content_id} not found")
            return
        
        # Check if already delivered
        if content.delivered:
            print(f"Content {content_id} already delivered, skipping")
            return
        
        # Get the topic
        topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
        if not topic:
            print(f"Error: Topic with id {content.topic_id} not found")
            return
        
        # Get all subscribers for this topic
        subscribers = db.query(TopicSubscriber).filter(
            TopicSubscriber.topic_id == content.topic_id
        ).all()
        
        if not subscribers:
            print(f"No subscribers found for topic {content.topic_id}")
            # Mark as delivered even if no subscribers
            content.delivered = True
            db.commit()
            return
        
        # Initialize SendGrid client
        if not SENDGRID_API_KEY:
            print("Error: SENDGRID_API_KEY not configured")
            print("⚠️  Check Render environment variables - SENDGRID_API_KEY is missing or empty")
            return
        
        if not SENDGRID_FROM_EMAIL:
            print("Error: SENDGRID_FROM_EMAIL not configured")
            print("⚠️  Check Render environment variables - SENDGRID_FROM_EMAIL is missing or empty")
            return
        
        # Log configuration status (without exposing full API key)
        api_key_preview = f"{SENDGRID_API_KEY[:10]}..." if len(SENDGRID_API_KEY) > 10 else "INVALID"
        print(f"SendGrid Config: API Key starts with {api_key_preview}, From: {SENDGRID_FROM_EMAIL}")
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Send email to each subscriber
        success_count = 0
        error_count = 0
        
        for subscriber in subscribers:
            try:
                message = Mail(
                    from_email=SENDGRID_FROM_EMAIL,
                    to_emails=subscriber.email,
                    subject=f"Newsletter: {topic.name}",
                    html_content=content.content_text
                )
                
                response = sg.send(message)
                
                if response.status_code in [200, 202]:
                    success_count += 1
                    print(f"Email sent successfully to {subscriber.email}")
                else:
                    error_count += 1
                    # Try to get error details from response
                    try:
                        error_body = response.body.decode('utf-8') if response.body else "No error details"
                        print(f"Failed to send email to {subscriber.email}: Status {response.status_code}")
                        print(f"Error details: {error_body}")
                    except:
                        print(f"Failed to send email to {subscriber.email}: Status {response.status_code}")
                    
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                print(f"Error sending email to {subscriber.email}: {error_msg}")
                
                # Provide helpful error messages for common issues
                if "403" in error_msg or "Forbidden" in error_msg:
                    print("⚠️  SendGrid 403 Forbidden - Common causes:")
                    print("   1. API key is invalid or doesn't have 'Mail Send' permissions")
                    print("   2. Sender email is not verified in SendGrid")
                    print("   3. SendGrid account is suspended or needs verification")
                    print("   4. Free tier daily limit (100 emails) exceeded")
                    print(f"   Check: SendGrid Dashboard → Settings → Sender Authentication")
                    print(f"   Verify sender: {SENDGRID_FROM_EMAIL}")
                
                traceback.print_exc()
        
        # Mark content as delivered
        content.delivered = True
        db.commit()
        
        print(f"Newsletter delivery completed for content {content_id}: {success_count} successful, {error_count} failed")
        
    except Exception as e:
        print(f"Error in send_newsletter task: {e}")
        traceback.print_exc()
        if db:
            db.rollback()
    finally:
        if db:
            db.close()
            # Explicitly remove reference to help garbage collection
            db = None

