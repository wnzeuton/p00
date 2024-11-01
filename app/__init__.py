# DATA TABLE

import sqlite3, csv
import bcrypt

DB_FILE = "xase.db"

db = sqlite3.connect(DB_FILE)
c = db.cursor()

# CREATING DATA TABLES

# USER TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_username TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
''')

# CATEGORIES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE
);
''')

# POSTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date DATE,
    category INTEGER,
    author_id INTEGER,
    content TEXT,
    FOREIGN KEY (author_id) REFERENCES users(id)
);
''')

# COMMENTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    date DATE,
    author_id INTEGER,
    post_id INTEGER,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
);
''')

db.commit()
db.close()


import os
from flask import Flask, render_template, request, session, redirect

app = Flask(__name__)
app.secret_key = os.urandom(32)
def sign_in_state():
    return 'user' in session.keys() and session['user'] != None
def password_hash(password, salt):
    if(salt == ""):
        salt = bcrypt.gensalt()
    return [bcrypt.hashpw(password.encode('utf-8'), salt), salt]
@app.route("/", methods = ['GET', 'POST'])
def home():
    return render_template("index.html", guest = not sign_in_state(), username = session['user'][2] if sign_in_state() else "")

@app.route("/blog")
def blog():
    return render_template("blogpost.html")

@app.route("/edit")
def edit():
    return render_template("editpost.html")

@app.route("/login", methods = ['GET', 'POST'])
def login():
    error = ""
    if(sign_in_state()):
        return redirect('/')
    email = (request.form.get('email'))
    if(email != None):
        conn = sqlite3.connect('xase.db')
        c = conn.cursor()
        try:
            c.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
            user = c.fetchone()
        except sqlite3.Error as e:
            error = e
        finally:
            c.close()
            conn.close()
        if(user == None):
            return render_template("login.html", message = 'No such user with that email')
        print(password_hash(request.form.get('password'), user[4])[0])
        if(password_hash(request.form.get('password'), user[4])[0]
            != user[3]):
            return render_template("login.html", message = "Incorrect password")
        session['user'] = user
        return redirect('/')   
    else:
        return render_template("login.html", message = error)
@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/category")
def category():
    return render_template("category.html")

@app.route("/signup", methods = ['GET', 'POST'])
def signup():
    error = []
    if(len(request.form) != 0):
        pwd_salt = password_hash(request.form.get('password'), "")
        new_user = (request.form.get('username').lower(), request.form.get('username'), pwd_salt[0], pwd_salt[1], request.form.get('email').lower())
        conn = sqlite3.connect('xase.db')
        c = conn.cursor()
        try:
            c.execute('''
            INSERT INTO users (normalized_username, username, password, salt, email) VALUES (?, ?, ?, ?, ?)
            ''', new_user)
            conn.commit()
            c.execute("SELECT MAX(Id) FROM users")
            session['user'] = (c.fetchone(), new_user[0], new_user[1], new_user[2], new_user[3], new_user[4])
        except sqlite3.IntegrityError:
            error.append("An account with that username or email already exists")
            conn.rollback()
        except sqlite3.Error as e:
            error.append(f"ERROR: {e} - CONTACT DEVELOPERS FOR HELP")
            conn.rollback()
        finally:
            c.close()
            conn.close()
        if(len(error) == 0):
            if any(c in " `~!@#$%^&*()=+[]\{\}\|,./<>?;\':\"" for c in request.form.get('username')):
                error.append("Username shouldn't contain special characters")
            if(len(request.form.get('password')) < 10):
                error.append("Password must be at least 10 characters long")
            if(request.form.get('password') != request.form.get('confirm_password')):
                error.append("Passwords do not match")
        
    if(len(error) == 0 and len(request.form) != 0):
        print(session['user'])
        return redirect('/')
    return render_template("signup.html", message = error)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/')

if __name__ == "__main__":
    app.debug = True 
    app.run()