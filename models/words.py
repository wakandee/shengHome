from . import db
from sqlalchemy.sql import func

class words(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False, unique=True)
    translation = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    credits = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    synonyms = db.relationship('synonyms', backref='word', lazy=True)
    votes = db.relationship('word_votes', backref='word', lazy=True)
