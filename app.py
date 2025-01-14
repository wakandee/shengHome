from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash
from config import Config
from models import db
from models import User
from utils.db_helper import check_and_create_db
from flask_migrate import Migrate
import json
from sqlalchemy import inspect  # Import inspect

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

print(app.config['SQLALCHEMY_DATABASE_URI'])
db.init_app(app)

# Check if the table exists using the inspect method
with app.app_context():
    inspector = inspect(db.engine)  # Create an inspector object
    if 'users' not in inspector.get_table_names():  # Check if 'users' table exists
        db.create_all()  # This will create the users table if it does not exist

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

from models import User  # Make sure you import the User model

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
            
            # Check if the username exists and the password matches
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                error_login = "Invalid credentials"
                return render_template("login_register.html", translations=translations, tab='login', error_login=error_login)
        
        elif form_type == 'register':
            name = request.form['name']
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
        
            # Check if passwords match
            if password != confirm_password:
                flash("Passwords do not match. Please try again.", "error_signup")
                return render_template('login_register.html', translations=translations, tab='signup',  error_signup="Passwords do not match")

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
                new_user = User(username=username, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login_register'))   
    
    return render_template('login_register.html', translations=translations)



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

if __name__ == '__main__':
    app.run(debug=True)
