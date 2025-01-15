from . import db

from sqlalchemy import Enum  # Add this import at the top of your file

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # First name and other name
    fname = db.Column(db.String(100), nullable=False)  # First name
    other_name = db.Column(db.String(100), nullable=False)  # Other name (replaces lname)

    # Updated Enum for status
    status = db.Column(
        Enum('pending', 'verified', 'suspended', name='status_enum'),
        nullable=False,
        default='pending'
    )
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Avatar(db.Model):
    __tablename__ = 'avatars'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    avatar_url = db.Column(db.String(255), nullable=False)  # URL or file path to the avatar image
    uploaded_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    # Relationship with the User model
    user = db.relationship('User', backref=db.backref('avatar', uselist=False, cascade="all, delete-orphan"))