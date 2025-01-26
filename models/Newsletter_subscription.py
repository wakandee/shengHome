from . import db
from sqlalchemy.sql import func

class NewsletterSubscription(db.Model):
    __tablename__ = 'newsletter_subscriptions'
    
    subscription_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Email of the subscriber
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Foreign Key to User
    subscribed_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)  # Date of subscription
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('newsletter_subscriptions', lazy=True))
