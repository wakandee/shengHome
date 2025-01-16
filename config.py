import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:admin@localhost/sheng_home_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'
    DEFAULT_AVATAR_FILENAME = 'default-avatar.png'

    # Set the path for avatar uploads inside the static folder
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads', 'avatars')  # Adjust path for avatar uploads


    # @staticmethod
    # def init_app(app):
    #     # Set the upload folder relative to Flask's static folder after the app is initialized
    #     app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads', 'avatars')

    # Flask-Mail configuration
    # General configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465  # Use 587 for TLS
    MAIL_USE_SSL = True  # Set to False if using TLS
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')  # Get email from environment variable
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'your-app-password')  # Get password from environment variable
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
