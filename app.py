from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash
from config import Config # Import configuration settings
from models import db, User, Avatar, UserVerification, Categories, synonyms, word_votes, words, Artist,Song
from utils.db_helper import check_and_create_db
from flask_migrate import Migrate
import datetime
from sqlalchemy import inspect  # Import inspect
from sqlalchemy import func, case
import hashlib # for hashing password into Sha256
from werkzeug.utils import secure_filename, os
from datetime import datetime, timedelta
import random, json

from flask import jsonify


from flask_mail import Mail
from dotenv import load_dotenv  # Load environment variables from .env file
from utils import send_email  # Import the send_email function from utils.py 
from models import Categories 

# Load environment variables from .env file
load_dotenv()

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
    required_tables = ['users', 'avatars', 'user_verifications', 'word_votes', 'synonyms', 'words', 'categories', 'artist','artist_songs']
    
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

    words_list = get_words_with_votes()
    words_list_trimmed = words_list[:len(words_list) // 2]  # Slicing the list to 1/3 of its original length
    
    # Load the corresponding language file from the 'locales' folder
    translations = load_language(language)
    
    # Render the HTML template with translations passed to it
    return render_template('home.html', translations=translations, words_list=words_list, words_list_trimmed=words_list_trimmed)

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


def get_votes():
    # Query the word_votes table to calculate upvotes and downvotes for each word
    votes_data = db.session.query(
        word_votes.word_id,
        func.sum(case((word_votes.vote_type == True, 1), else_=0)).label('upvotes'),
        func.sum(case((word_votes.vote_type == False, 1), else_=0)).label('downvotes'),
        (
            func.sum(case((word_votes.vote_type == True, 1), else_=0)) -
            func.sum(case((word_votes.vote_type == False, 1), else_=0))
        ).label('votes')
    ).group_by(word_votes.word_id).all()

    return votes_data

def get_words_with_votes():
    # Retrieve votes data
    votes_data = get_votes()
    votes_dict = {vote.word_id: vote.votes for vote in votes_data}

    # Query words and join with User table
    query_result = db.session.query(
        words,
        User.fname,
        User.other_name
    ).join(User, words.created_by == User.user_id).all()

    # Map results to ORM instances with added attributes
    words_with_votes = []
    for word, fname, other_name in query_result:
        word.votes_count = votes_dict.get(word.id, 0)  # Default to 0 votes
        word.creator_name = f"{fname} {other_name}"  # Combine creator's name
        words_with_votes.append(word)

    return words_with_votes


def search_words_with_votes(search_query):
    # Build the query to calculate votes
    votes_query = db.session.query(
        word_votes.word_id,
        (
            func.sum(case((word_votes.vote_type == True, 1), else_=0)) -
            func.sum(case((word_votes.vote_type == False, 1), else_=0))
        ).label('votes')
    ).group_by(word_votes.word_id).subquery()

    # Query words with filtering and join with votes and User table
    query_result = db.session.query(
        words,
        func.coalesce(votes_query.c.votes, 0).label('votes_count'),
        User.fname,
        User.other_name
    ).outerjoin(votes_query, words.id == votes_query.c.word_id)\
     .join(User, words.created_by == User.user_id)

    if search_query:
        query_result = query_result.filter(words.word.ilike(f"%{search_query}%"))

    # Map results to ORM instances with added attributes
    words_with_votes = []
    for word, votes_count, fname, other_name in query_result.all():
        word.votes_count = votes_count
        word.creator_name = f"{fname} {other_name}"
        words_with_votes.append(word)

    return words_with_votes




@app.route('/translate', methods=['GET', 'POST'])
def translate():
    search_query = request.args.get('q', '').strip()  # Get the search query from the URL params

    if search_query:
        words_list = search_words_with_votes(search_query)
    else:
        words_list = get_words_with_votes()

    # Handle AJAX request by checking the "X-Requested-With" header
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([
            {
                "id": word.id,
                "word": word.word,
                "translation": word.translation,
                "example": word.example,
                "synonyms": [synonym.name for synonym in word.synonyms],
                "creator_name": word.creator_name,  # Include creator's full name
                "votes": word.votes_count  # Include computed votes
            } for word in words_list
        ])

    language = request.cookies.get('language') or 'en'
    translations = load_language(language)

    # Render the full page for non-AJAX requests
    return render_template('translate.html', translations=translations, words=words_list)




@app.route('/word/vote', methods=['POST'])
def vote_word():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized, Please Sign in First"}), 401  # User not logged in

    user_id = session['user_id']
    word_id = request.json.get('word_id')
    vote_type = request.json.get('vote_type')  # True for upvote, False for downvote

    # Validate input
    if word_id is None or vote_type not in [True, False]:
        return jsonify({"error": "Invalid request"}), 400

    # Check if the user already voted for this word
    existing_vote = word_votes.query.filter_by(user_id=user_id, word_id=word_id).first()

    if existing_vote:
        return jsonify({"error": "You have already voted this way."}), 400
        # if existing_vote.vote_type == vote_type:
        # if existing_vote.vote_type:
        #     return jsonify({"error": "You have already voted this way."}), 400
        # else:
        #     # Update the vote type if the user changes their vote
        #     existing_vote.vote_type = vote_type
        #     db.session.commit()
        #     return jsonify({"message": "Vote updated successfully."}), 200

    # Add a new vote
    new_vote = word_votes(
        word_id=word_id,
        vote_type=vote_type,
        user_id=user_id
    )
    db.session.add(new_vote)
    db.session.commit()
    return jsonify({"message": "Vote added successfully."}), 201


@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    if request.method == 'POST':
        word = request.form['word']
        translation = request.form['translation']
        example = request.form['example']
        category_id = request.form['category']
        credits = request.form['credits']
        user_id = session.get('user_id')  # Assuming user_id is stored in the session

        # Create a new word entry
        new_word = words(
            word=word,
            translation=translation,
            example=example,
            category_id=category_id,
            credits=credits,
            created_by=user_id,
        )
        db.session.add(new_word)
        db.session.commit()
        return redirect(url_for('translate'))

    # Use a different name for the variable to avoid conflict with the model name
    all_categories = Categories.query.all()  # Preload all categories
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('add_word.html', translations=translations, categories=all_categories)

# @app.route('/word/vote', methods=['POST'])
# def vote_word():
#     if 'user_id' not in session:
#         flash("Unauthorized. Please log in to vote.", "error")
#         return jsonify({"status": "error", "flash": "Unauthorized. Please log in to vote."}), 401

#     user_id = session['user_id']
#     word_id = request.json.get('word_id')
#     vote_type = request.json.get('vote_type')  # True for upvote, False for downvote

#     # Validate input
#     if word_id is None or vote_type not in [True, False]:
#         flash("Invalid vote request.", "error")
#         return jsonify({"status": "error", "flash": "Invalid vote request."}), 400

#     # Check if the user already voted for this word
#     existing_vote = word_votes.query.filter_by(user_id=user_id, word_id=word_id).first()

#     if existing_vote:
#         if existing_vote.vote_type == vote_type:
#             flash("You have already voted this way.", "error")
#             return jsonify({"status": "error", "flash": "You have already voted this way."}), 400
#         else:
#             # Update the vote type if the user changes their vote
#             existing_vote.vote_type = vote_type
#             db.session.commit()
#             flash("Your vote has been updated successfully.", "success")
#             return jsonify({"status": "success", "flash": "Your vote has been updated successfully."}), 200

#     # Add a new vote
#     new_vote = word_votes(
#         word_id=word_id,
#         vote_type=vote_type,
#         user_id=user_id
#     )
#     db.session.add(new_vote)
#     db.session.commit()
#     flash("Your vote has been added successfully.", "success")
#     return jsonify({"status": "success", "flash": "Your vote has been added successfully."}), 201




# @app.route('/categories')
# def categories():
#     language = request.cookies.get('language') or 'en'
#     translations = load_language(language)
#     return render_template('categories.html', translations=translations)

@app.route('/categories')
def categories():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    all_categories = Categories.query.all()
    return render_template('categories.html',translations=translations, categories=all_categories)

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        category_description = request.form.get('category_description')
        is_special = 'is_special' in request.form  # Checkbox for special category
        created_by = session.get('user_id')  # Fetch user_id from session
        
        if category_name:
            new_category = Categories(
                name=category_name,
                description=category_description,
                is_special=is_special,
                created_by=created_by
            )
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('categories'))
        else:
            flash('Category name is required!', 'error')
    
    return render_template('add_category.html', translations=translations)


@app.route('/category/<int:category_id>')
def view_category(category_id):
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    category = categories.query.get_or_404(category_id)
    return render_template('words.html', translations=translations, category=category, words=category.words)

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

@app.route('/add_artist', methods=['GET', 'POST'])
def add_artist():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized, Please Sign in First"}), 401  # User not logged in

    if request.method == 'POST':
        artist_name = request.form.get('artist_name')
        artist_description = request.form.get('artist_description')
        created_by = session.get('user_id')  # Fetch user_id from session

        # Check if the artist name already exists
        existing_artist = Artist.query.filter_by(name=artist_name).first()

        if existing_artist:
            flash(f"Artist '{artist_name}' already exists!", 'error')
        else:
            if artist_name:
                new_artist = Artist(
                    name=artist_name,
                    description=artist_description,
                    created_by=created_by
                )
                db.session.add(new_artist)
                db.session.commit()
                flash('Artist Added Successfully', 'success')
                return redirect(url_for('add_artist'))
            else:
                flash('Artist Name Required', 'error')

    return render_template('add_artist.html', translations=translations)




@app.route('/add_song', methods=['GET', 'POST'])
def add_song():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized, Please Sign in First"}), 401  # User not logged in

    artists = Artist.query.all()  # Fetch all available artists for the dropdown

    if request.method == 'POST':
        song_title = request.form.get('song_title')
        song_description = request.form.get('song_description')
        artist_id = request.form.get('artist_id')
        created_by = session.get('user_id')  # Fetch user_id from session

        if song_title and artist_id:
            new_song = Song(
                title=song_title,
                description=song_description,
                artist_id=int(artist_id),
                created_by=created_by
            )
            db.session.add(new_song)
            db.session.commit()
            flash(translations['song_added_successfully'], 'success')
            return redirect(url_for('add_song'))
        else:
            flash(translations['song_title_and_artist_required'], 'error')

    return render_template('add_song.html', translations=translations, artists=artists)



@app.route('/articles')
def articles():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('articles.html', translations=translations)


@app.route('/statistics')
def statistics():
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    return render_template('statistics.html', translations=translations)

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
