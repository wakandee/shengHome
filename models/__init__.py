from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()

# Import the models (e.g., User)
from .user import User
from .Avatar import Avatar
from .UserVerification import UserVerification
# from models.translation import Translation  # Add other models here if necessary
