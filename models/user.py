from . import db
from sqlalchemy import Enum  # Add this import at the top of your file
from sqlalchemy.sql import func

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    # First name and other name
    fname = db.Column(db.String(100), nullable=False)  # First name
    other_name = db.Column(db.String(100), nullable=False)  # Other name (replaces lname)

    # Updated Enum for status
    status = db.Column(
        Enum('pending', 'active', 'suspended', name='status_enum'),
        nullable=False,
        default='pending'
    )
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # Add this column
    password = db.Column(db.String(255), nullable=False)

    # New column to capture date created
    date_created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationship to Articles
    articles = db.relationship('Article', back_populates='user', lazy=True)
