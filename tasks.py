import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery_app import celery_app
from sqlalchemy.orm import Session
import traceback
from database import SessionLocal
from models import Content, TopicSubscriber, Topic
from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_USE_TLS
)

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email using SMTP.
    Returns True if successful, False otherwise.
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        
        if SMTP_USE_TLS:
            server.starttls()
        
        # Login if credentials are provided
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SMTP_FROM_EMAIL, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        return False

@celery_app.task(name="tasks.send_newsletter")
def send_newsletter(content_id: int):
    """
    Celery task to send newsletter to all subscribers of a topic.
    This task is triggered when content is created.
    """
    db: Session = SessionLocal()
    try:
        # Get the content
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            print(f"Content with id {content_id} not found")
            return {"status": "error", "message": f"Content {content_id} not found"}
        
        # Get all subscribers for this topic
        subscribers = db.query(TopicSubscriber).filter(
            TopicSubscriber.topic_id == content.topic_id
        ).all()
        
        # Get topic name
        topic = db.query(Topic).filter(Topic.id == content.topic_id).first()
        topic_name = topic.name if topic else "Unknown Topic"
        topic_description = topic.description if topic else ""
        
        # Prepare email content
        subject = f"Newsletter: {topic_name}"
        email_body = f"""
            Hello!

            You're receiving this newsletter for the topic: {topic_name}
            {topic_description and f'Description: {topic_description}' or ''}

            ---

            {content.content_text}

            ---

            Thank you for subscribing!
            """
        
        # Send newsletter to each subscriber
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        for subscriber in subscribers:
            success = send_email(subscriber.email, subject, email_body)
            if success:
                sent_count += 1
                print(f"✓ Newsletter sent to {subscriber.email} for topic '{topic_name}'")
            else:
                failed_count += 1
                failed_emails.append(subscriber.email)
                print(f"✗ Failed to send newsletter to {subscriber.email}")
        
        # Mark content as delivered if at least one email was sent successfully
        if sent_count > 0:
            content.delivered = True
            db.commit()
        
        result = {
            "status": "success",
            "content_id": content_id,
            "topic_id": content.topic_id,
            "topic_name": topic_name,
            "subscribers_count": len(subscribers),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "delivered": content.delivered
        }
        
        if failed_emails:
            result["failed_emails"] = failed_emails
        
        return result
    except Exception as e:
        print(f"Error sending newsletter for content {content_id}: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

