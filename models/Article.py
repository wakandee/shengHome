from . import db
from sqlalchemy.sql import func


class Article(db.Model):
    __tablename__ = 'articles'
    article_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='articles')

    # Relationship to Votes
    votes = db.relationship('Article_Vote', backref='article', lazy=True)



# Vote Model
class Article_Vote(db.Model):
    __tablename__ = 'articles_votes'
    vote_id = db.Column(db.Integer, primary_key=True)
    vote_type = db.Column(db.Boolean, nullable=False)  # True for upvote, False for downvote
    # value = db.Column(db.Integer, nullable=False)  # 1 for upvote, -1 for downvote
    article_id = db.Column(db.Integer, db.ForeignKey('articles.article_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
