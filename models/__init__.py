from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()

# Import the models (e.g., User)
from .user import User
from .Avatar import Avatar
from .UserVerification import UserVerification
from .words import words
from .word_votes import word_votes
from .synonyms import synonyms
from .categories import Categories
from .Artist import Artist
from .Artist import Song
# from models.translation import Translation  # Add other models here if necessary
