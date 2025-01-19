from . import db
from sqlalchemy.sql import func

class word_votes(db.Model):
    __tablename__ = 'word_votes'
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    vote_type = db.Column(db.Boolean, nullable=False)  # True for upvote, False for downvote
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
