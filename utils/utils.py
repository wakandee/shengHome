# utils.py
from flask_mail import Message
from flask_mail import Mail

# Initialize the Mail object (this is done in the main Flask app)
mail = Mail()

# Reusable function for sending email
def send_email(app, subject, recipient, body):
    with app.app_context():  # Ensure Flask app context is available
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        mail.send(msg)
