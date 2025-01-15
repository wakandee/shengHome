from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()

# Import the models (e.g., User)
from .user import User
from .user import Avatar
# from models.translation import Translation  # Add other models here if necessary
