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
    db = SessionLocal()
    try:
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
            return
        
        if not SENDGRID_FROM_EMAIL:
            print("Error: SENDGRID_FROM_EMAIL not configured")
            return
        
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
                    print(f"Failed to send email to {subscriber.email}: Status {response.status_code}")
                    
            except Exception as e:
                error_count += 1
                print(f"Error sending email to {subscriber.email}: {e}")
                traceback.print_exc()
        
        # Mark content as delivered
        content.delivered = True
        db.commit()
        
        print(f"Newsletter delivery completed for content {content_id}: {success_count} successful, {error_count} failed")
        
    except Exception as e:
        print(f"Error in send_newsletter task: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

