from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy data for demonstration purposes
users = {"testuser": "password"}

@app.route('/')
def home():
    return render_template('home.html')

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
                
    return render_template('login_register.html')

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
        return render_template('translate.html', translated_word=translated_word)
    return render_template('translate.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/trending_phrases')
def trending_phrases():
    return render_template('trending_phrases.html')

@app.route('/lyrics')
def lyrics():
    return render_template('lyrics.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
