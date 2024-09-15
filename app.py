from flask import Flask, render_template, request, redirect, url_for, session, make_response
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy data for demonstration purposes
users = {"testuser": "password"}

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

@app.route('/login_register', methods=['GET', 'POST'])
def login_register():
    if request.method == 'POST':
        form_type = request.form['form_type']
        username = request.form['username']
        password = request.form['password']
        
        if form_type == 'login':
            if username in users and users[username] == password:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return "Invalid credentials!"
        elif form_type == 'register':
            if username not in users:
                users[username] = password
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return "User already exists!"
                
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('login_register.html', translations=translations)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/translate', methods=['GET', 'POST'])
def translate():
    if request.method == 'POST':
        sheng_word = request.form['sheng_word']
        # Add translation logic here
        translated_word = "Example Translation"  # Replace with actual translation
        # Detect the user's preferred language from a cookie or default to 'en' (English)
        language = request.cookies.get('language') or 'en'
        translations = load_language(language)
        return render_template('translate.html', translated_word=translated_word, translations=translations)
    
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('translate.html', translations=translations)

@app.route('/categories')
def categories():
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('categories.html', translations=translations)

@app.route('/trending_phrases')
def trending_phrases():
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('trending_phrases.html', translations=translations)

@app.route('/lyrics')
def lyrics():
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('lyrics.html', translations=translations)

@app.route('/about')
def about():
    # Detect the user's preferred language from a cookie or default to 'en' (English)
    language = request.cookies.get('language') or 'en'
    translations = load_language(language)
    
    return render_template('about.html', translations=translations)

if __name__ == '__main__':
    app.run(debug=True)
