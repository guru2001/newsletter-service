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
            print("❌ Error: SENDGRID_API_KEY not configured")
            print("   Please set SENDGRID_API_KEY environment variable")
            return
        
        if not SENDGRID_FROM_EMAIL:
            print("❌ Error: SENDGRID_FROM_EMAIL not configured")
            print("   Please set SENDGRID_FROM_EMAIL environment variable")
            return
        
        # Validate API key format (SendGrid API keys start with 'SG.')
        if not SENDGRID_API_KEY.startswith('SG.'):
            print(f"⚠️  WARNING: SENDGRID_API_KEY doesn't appear to be a valid SendGrid API key")
            print(f"   SendGrid API keys typically start with 'SG.'")
            print(f"   Current key starts with: {SENDGRID_API_KEY[:10]}...")
        
        print(f"📧 Using SendGrid with FROM email: {SENDGRID_FROM_EMAIL}")
        print(f"🔑 API Key configured: {SENDGRID_API_KEY[:10]}...{SENDGRID_API_KEY[-4:] if len(SENDGRID_API_KEY) > 14 else '***'}")
        
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
                
                # Get response details for debugging
                status_code = response.status_code
                response_headers = dict(response.headers) if response.headers else {}
                response_body = ""
                try:
                    if response.body:
                        response_body = response.body.decode('utf-8')
                except:
                    response_body = str(response.body) if response.body else ""
                
                # Log full response for debugging
                print(f"SendGrid response for {subscriber.email}:")
                print(f"  Status Code: {status_code}")
                print(f"  Headers: {response_headers}")
                print(f"  Body: {response_body}")
                
                # Check if email was actually accepted
                if status_code in [200, 202]:
                    # Even with 200/202, check response body for errors
                    if response_body and ('error' in response_body.lower() or 'unauthorized' in response_body.lower()):
                        error_count += 1
                        print(f"⚠️  WARNING: SendGrid returned {status_code} but response contains errors for {subscriber.email}")
                        print(f"   Response: {response_body}")
                    else:
                        success_count += 1
                        print(f"✅ Email sent successfully to {subscriber.email}")
                else:
                    error_count += 1
                    print(f"❌ Failed to send email to {subscriber.email}: Status {status_code}")
                    print(f"   Error details: {response_body}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Exception sending email to {subscriber.email}: {e}")
                print(f"   Exception type: {type(e).__name__}")
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

