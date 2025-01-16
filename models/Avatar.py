from . import db

class Avatar(db.Model):
    __tablename__ = 'avatars'
    avatar_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=False)  # URL or file path to the avatar image
    uploaded_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    # Relationship with the User model
    user = db.relationship('User', backref=db.backref('avatars', lazy='dynamic', cascade="all, delete-orphan"))
