import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def send_email_notification(to_email, subject, body):
    """Send email notification using SMTP."""
    try:
        # Debug: Print current working directory and .env file contents
        print("Current working directory:", os.getcwd())
        print("Checking if .env file exists:", os.path.exists('.env'))
        
        # Email configuration
        sender_email = os.getenv('EMAIL_USER', 'summerofai05@gmail.com')
        sender_password = os.getenv('EMAIL_PASSWORD', 'your_app_password_here')  # Replace with your actual app password
        
        print("\nEmail Configuration:")
        print(f"Sender Email: {sender_email}")
        print(f"Password length: {len(sender_password) if sender_password else 0}")
        print(f"Recipient: {to_email}")
        print(f"Subject: {subject}")
        
        if not sender_email or not sender_password:
            print("\nError: Email configuration missing!")
            print("EMAIL_USER:", "Set" if sender_email else "Not set")
            print("EMAIL_PASSWORD:", "Set" if sender_password else "Not set")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Gmail SMTP configuration
        print("\nConnecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Enable SMTP debugging
        server.starttls()
        
        print("Attempting to login...")
        try:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print("Email sent successfully!")
            return True
        except smtplib.SMTPAuthenticationError:
            print("\nError: SMTP Authentication failed. Please check your email and app password.")
            return False
        except Exception as e:
            print(f"\nError sending email: {str(e)}")
            return False
    except Exception as e:
        print(f"\nError in email configuration: {str(e)}")
        return False

# Test email function
def test_email_configuration():
    """Test the email configuration."""
    print("\nTesting email configuration...")
    test_email = "summerofai2025@gmail.com"
    test_subject = "Test Email from Intern Task Timeline Tracker"
    test_body = "This is a test email to verify the email configuration."
    
    success = send_email_notification(test_email, test_subject, test_body)
    if success:
        print("\nEmail test successful!")
    else:
        print("\nEmail test failed!")
    return success

def send_task_assignment_notification(task, user):
    """Send notification when a task is assigned."""
    subject = f"New Task Assigned: {task.title}"
    body = f"""
    Dear {user.username},

    A new task has been assigned to you:

    Task: {task.title}
    Description: {task.description}
    Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}

    Please log in to the Intern Task Timeline Tracker to view more details and update the status.

    Best regards,
    Intern Task Timeline Tracker
    """
    return send_email_notification(user.email, subject, body)

def send_task_update_notification(task, user, new_status):
    """Send notification when a task status is updated."""
    subject = f"Task Status Updated: {task.title}"
    body = f"""
    Dear {user.username},

    The status of your task has been updated:

    Task: {task.title}
    New Status: {new_status.value}
    Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}

    Please log in to the Intern Task Timeline Tracker to view more details.

    Best regards,
    Intern Task Timeline Tracker
    """
    return send_email_notification(user.email, subject, body)

def send_task_completion_notification(task, user):
    """Send notification when a task is completed."""
    completion_time = datetime.now()
    time_diff = completion_time - task.deadline
    
    subject = f"Task Completed: {task.title}"
    body = f"""
    Dear {user.username},

    Congratulations! You have completed the following task:

    Task: {task.title}
    Completion Time: {completion_time.strftime('%Y-%m-%d %H:%M')}
    Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}
    """
    
    if time_diff.total_seconds() > 0:
        body += f"\nTask was completed {format_timedelta(time_diff)} after the deadline."
    else:
        body += f"\nTask was completed {format_timedelta(abs(time_diff))} before the deadline!"
    
    body += "\n\nBest regards,\nIntern Task Timeline Tracker"
    
    return send_email_notification(user.email, subject, body)

def check_overdue_tasks(tasks):
    """Check for overdue tasks and send notifications."""
    now = datetime.utcnow()
    overdue_tasks = [task for task in tasks if task.deadline < now and task.status != TaskStatus.COMPLETED]
    
    for task in overdue_tasks:
        subject = f"Task Overdue: {task.title}"
        body = f"""
        Dear {task.user.username},
        
        Your task "{task.title}" is overdue. Please update its status or complete it as soon as possible.
        
        Task Details:
        - Description: {task.description}
        - Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}
        - Current Status: {task.status.value}
        
        Best regards,
        Intern Task Timeline Tracker
        """
        send_email_notification(task.user.email, subject, body)

def get_upcoming_deadlines(tasks, days=7):
    """Get tasks with deadlines in the next X days."""
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    return [task for task in tasks if now <= task.deadline <= future]

def calculate_completion_rate(tasks):
    """Calculate task completion rate."""
    if not tasks:
        return 0
    completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    return (completed / len(tasks)) * 100

def format_timedelta(delta):
    """Format timedelta into human-readable string."""
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days} days, {hours} hours"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    else:
        return f"{minutes} minutes"

def get_task_status_color(status):
    """Get color for task status."""
    colors = {
        'not_started': 'gray',
        'in_progress': 'yellow',
        'completed': 'green',
        'overdue': 'red'
    }
    return colors.get(status, 'gray')

# Add this at the end of the file
if __name__ == "__main__":
    test_email_configuration()