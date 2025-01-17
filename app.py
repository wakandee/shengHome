from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash
from config import Config
from models import db
from models import User  # Make sure you import the User model
from models import Avatar, UserVerification
from utils.db_helper import check_and_create_db
from flask_migrate import Migrate
import json
import datetime
from sqlalchemy import inspect  # Import inspect
import hashlib # for hashing password into Sha256
from werkzeug.utils import secure_filename, os
from datetime import datetime, timedelta
import random

from flask import request, jsonify, url_for


from flask_mail import Mail
from dotenv import load_dotenv  # Load environment variables from .env file

# Load environment variables from .env file
load_dotenv()

from utils import send_email  # Import the send_email function from utils.py
from config import Config  # Import configuration settings  


app = Flask(__name__)

# Define the database name you want to check
db_name = 'sheng_home_db'

# Check and create the database if it doesn't exist
check_and_create_db(db_name)

# Set the database URI before initializing the app
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:admin@localhost/sheng_home_db'


# Initialize SQLAlchemy and Flask-Migrate
app.secret_key = 'your_secret_key'
app.config.from_object(Config)

# print(app.config['SQLALCHEMY_DATABASE_URI'])
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Mail
mail = Mail(app)


# Config.init_app(app)  # Initialize the app with the custom upload folder

# Check and create if not exist the upload folder.
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Check and create tables
with app.app_context():
    inspector = inspect(db.engine)  # Create an inspector object
    
    # List of tables to check
    required_tables = ['users', 'avatars', 'user_verifications']
    
    existing_tables = inspector.get_table_names()  # Fetch existing tables
    
    # Check for missing tables and create them
    for table in required_tables:
        if table not in existing_tables:
            print(f"Creating table: {table}")
            db.create_all()  # This will create all missing tables defined in the models

@app.route('/set_language/<lang>')
def set_language(lang):
    # Set a cookie to remember the user's selected language
    response = make_response(redirect(url_for('home')))
    response.set_cookie('language', lang, max_age=60*60*24*30)  # Store for 30 days
    return response

# Helper function to load the appropriate language file
def load_language(lang):
    try:
        with open(f'locales/{lang}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open('locales/en.json', 'r') as f:
            return json.load(f)

@app.route('/')
def home():
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    
    # Load the corresponding language file from the 'locales' folder
    translations = load_language(language)
    
    # Render the HTML template with translations passed to it
    return render_template('home.html', translations=translations)

# Route to send email directly
@app.route('/send_email')
def send_email_route():
    send_email(app, 'Hello from Flask', 'allanwakande@gmail.com', 'This is a test email sent from Flask.')
    return 'Email sent!'

@app.route('/login_register', methods=['GET', 'POST'])
def login_register():
    
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)

    if request.method == 'POST':
        form_type = request.form['form_type']
        
        if form_type == 'login':
            username = request.form['username']
            password = request.form['password']
            
            # Fetch the user from the database
            user = User.query.filter_by(username=username).first()
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            
            if user and user.password == hashed_password:
                # Store user details in the session
                session['user_id'] = user.user_id
                session['username'] = user.username
                session['fname'] = user.fname
                session['other_name'] = user.other_name
                session['email'] = user.email
                session['status'] = user.status
                session['is_verified'] = user.is_verified

                # Fetch and store the avatar URL in session
                avatar = Avatar.query.filter_by(user_id=user.user_id).order_by(Avatar.uploaded_at.desc()).first()
                session['avatar_url'] = avatar.avatar_url if avatar else url_for('static', filename='default/avatars/default-avatar.png')
                return redirect(url_for('home'))
            else:
                error_login = "Invalid credentials"
                return render_template("login_register.html", translations=translations, tab='login', error_login=error_login)
        
        elif form_type == 'register':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Get the new fields from the form
            fname = request.form['fname']
            other_name = request.form['other_name']

            # Check if passwords match
            if password != confirm_password:
                flash("Passwords do not match. Please try again.", "error_signup")
                return render_template('login_register.html', translations=translations, tab='signup', error_signup="Passwords do not match")

            # Hash the password using SHA-256
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            # Check if username or email exists in the database
            existing_user = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_user:
                # User already exists
                return render_template('login_register.html', tab='signup', 
                                       translations=translations, error_signup="Username already exists!", 
                                       username=username, email=email)
            elif existing_email:
                # Email already exists
                return render_template('login_register.html', tab='signup', 
                                       translations=translations, error_signup="Email already exists!", 
                                       username=username, email=email)
            else:
                # Successful registration

                 # Generate a verification code and expiry time
                verification_code = str(random.randint(100000, 999999))
                # expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)  # 10 minutes expiry
                expiry_time = datetime.utcnow() + timedelta(minutes=10)

                new_user = User(username=username, email=email, password=hashed_password, fname=fname, other_name=other_name)
                db.session.add(new_user)
                db.session.commit()

                # Store the verification code in the database
                verification_record = UserVerification(user_id=new_user.user_id, code=verification_code, expiry_time=expiry_time)
                db.session.add(verification_record)
                db.session.commit()

                # Send the email with the verification code
                verification_link = url_for('verify_email', code=verification_code, _external=True)
                email_body = f'Hi {fname},\n\nPlease use the following code to verify your email address\n\n CODE: {verification_code}\n\n\n\n\nVerification link: {verification_link}\n\nThe code will expire in 10 minutes.'
                send_email(app, 'Email Verification', email, email_body)

                # session['email'] = user.email
                session['user_id'] = new_user.user_id

                flash("Registration successful! Please check your email to verify your account.", "success")
                # return render_template('email_verification.html', translations=translations)
                return redirect(url_for('email_verification'))  # Redirect to the verification page  
    
    return render_template('login_register.html', translations=translations)


@app.route('/verify_email', methods=['POST'])
def verify_email():
    verification_code = request.form.get('verificationCode')
    user_id = session.get('user_id')

    # Fetch the verification record
    verification_record = UserVerification.query.filter_by(
        user_id=user_id, code=verification_code
    ).first()

    # if verification_record and verification_record.expiry_time > datetime.datetime.utcnow():
    if verification_record and verification_record.expiry_time > datetime.utcnow():
        # Mark user as verified and update the status
        user = User.query.get(user_id)
        user.is_verified = True
        user.status = 'active'  # Update the status to 'active'
        db.session.commit()

        # Fetch updated user data and update session variables
        session['is_verified'] = user.is_verified
        session['status'] = user.status
        session['username'] = user.username
        session['email'] = user.email

        flash("Email verified successfully!", "success")
        return redirect(url_for('profile'))
    else:
        flash("Invalid or expired verification code.", "danger")
        return redirect(url_for('verify_email'))


@app.route('/email_verification')
def email_verification():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('email_verification.html', translations=translations)


@app.route('/resend_verification_code', methods=['POST'])
def resend_verification_code():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        verification_code = str(random.randint(100000, 999999))
        expiry_time = datetime.utcnow() + timedelta(minutes=10)

        # Update or create the verification record
        verification_record = UserVerification.query.filter_by(user_id=user.user_id).first()
        if verification_record:
            verification_record.code = verification_code
            verification_record.expiry_time = expiry_time
        else:
            verification_record = UserVerification(
                user_id=user.user_id, code=verification_code, expiry_time=expiry_time
            )
            db.session.add(verification_record)
        db.session.commit()

        # Send email
        email_body = f"Hi {user.fname},\n\nYour new verification code is: {verification_code}\nIt will expire in 10 minutes."
        send_email(app, "Resend Verification Code", email, email_body)

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'User not found'}), 404


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/translate', methods=['GET', 'POST'])
def translate():
    if request.method == 'POST':
        sheng_word = request.form['sheng_word']
        translated_word = "Example Translation"  # Replace with actual translation
        language = request.cookies.get('language') or 'en'
        translations = load_language(language)
        return render_template('translate.html', translated_word=translated_word, translations=translations)
    
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('translate.html', translations=translations)

@app.route('/categories')
def categories():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('categories.html', translations=translations)

@app.route('/trending_phrases')
def trending_phrases():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('trending_phrases.html', translations=translations)

@app.route('/lyrics')
def lyrics():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('lyrics.html', translations=translations)

@app.route('/about')
def about():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('about.html', translations=translations)

@app.route('/profile')
def profile():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    # Get the default avatar filename from  the config
    default_avatar_filename = app.config['DEFAULT_AVATAR_FILENAME']
    
    # Pass the default avatar filename to the template
    return render_template('profile.html', translations=translations, default_avatar_filename=default_avatar_filename)

@app.route('/change_password', methods=['POST'])
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('profile'))

    # Get the logged-in user's ID from the session
    user_id = session.get('user_id')
    if not user_id:
        flash('User is not logged in!', 'error')
        return redirect(url_for('login'))

    # Fetch the user from the database
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('login'))

    # Hash the provided current password and compare with the stored one
    hashed_current_password = hashlib.sha256(current_password.encode('utf-8')).hexdigest()
    if user.password != hashed_current_password:
        flash('Current password is incorrect!', 'error')
        return redirect(url_for('profile'))

    # Hash the new password and update it in the database
    hashed_new_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
    user.password = hashed_new_password
    db.session.commit()

    # Provide success feedback and redirect
    flash('Password updated successfully!', 'success')
    return redirect(url_for('profile'))

# Insert a new avatar into the database
def insert_avatar(user_id, avatar_url):
    """
    Inserts a new avatar record for the given user.

    :param user_id: ID of the user
    :param avatar_url: URL or path to the avatar file
    """
    new_avatar = Avatar(user_id=user_id, avatar_url=avatar_url)  # Avoid shadowing
    db.session.add(new_avatar)
    db.session.commit()

# Upload avatar endpoint
@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    avatar = request.files.get('avatar')
    user_id = session.get('user_id')  # Get user ID from the session
    
    if not avatar or not user_id:
        flash('Avatar and user ID are required.', 'danger')
        return redirect(url_for('profile'))

    # print(datetime)
    # Secure the filename and rename it using user_id, username, and timestamp
    filename = f"{user_id}_{session.get('username')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    # Save file to the UPLOAD_FOLDER
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

     # Set the URL for the avatar (Flask will serve this from the static folder)
    avatar_url = url_for('static', filename=f'uploads/avatars/{filename}')
    
    # Save the file to the server
    try:
        avatar.save(upload_path)
    except Exception as e:
        flash(f"Error uploading file: {str(e)}", 'danger')
        return redirect(url_for('profile'))

    # Insert avatar information into the database
    try:
        insert_avatar(user_id, avatar_url)
        # Update session with new avatar URL
        session['avatar_url'] = avatar_url
        flash('Avatar uploaded successfully!', 'success')
    except Exception as e:
        flash(f"Error saving avatar in database: {str(e)}", 'danger')
    
    return redirect(url_for('profile'))

@app.route('/admin')
def admin():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('admin.html', translations=translations)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
