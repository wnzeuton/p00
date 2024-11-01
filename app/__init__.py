# DATA TABLE

import sqlite3, csv
import bcrypt
import hashlib
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
    return 'username' in session.keys()
def password_hash(password):
    salt = str(bcrypt.gensalt())
    hashed = hashlib.md5((password+salt).encode())
    return hashed.hexdigest()
@app.route("/", methods = ['GET', 'POST'])
def home():
    return render_template("index.html", guest = not sign_in_state(), username = session['username'] if sign_in_state() else "")

@app.route("/blog")
def blog():
    return render_template("blogpost.html")

@app.route("/edit")
def edit():
    return render_template("editpost.html")

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if(sign_in_state()):
        return redirect('/')
    user = (request.form.get('username'))
    if(user != None):
        session['username'] = request.form.get('username')
        return redirect('/')   
    else:
        return render_template("login.html")
@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/category")
def category():
    return render_template("category.html")

@app.route("/signup", methods = ['GET', 'POST'])
def signup():
    error = ""
    if(len(request.form) != 0):
        new_user = (request.form.get('username').lower(), request.form.get('username'), password_hash(request.form.get('password')), request.form.get('email').lower())
        if(request.form.get('password') != request.form.get('confirm_password')):
            error = "Passwords do not match"
        if any(c in "`~!@#$%^&*()=+[]\{\}\|,./<>?;\':\"" for c in request.form.get('password')):
            error = "Username shouldn't contain special characters"
        if(error == ""):
            conn = sqlite3.connect('xase.db')
            c = conn.cursor()
            try:
                c.execute('''
                INSERT INTO users (normalized_username, username, password, email) VALUES (?, ?, ?, ?)
                ''', new_user)
                conn.commit()
            except sqlite3.IntegrityError:
                error = "An account with that username or email already exists"
            except sqlite3.Error as e:
                error = f"UNKOWN ERROR: {e} - CONTACT DEVELOPERS FOR HELP"
            finally:
                c.close()
                conn.close()
    if(error == "" and len(request.form) != 0):
        session['username'] = request.form.get('username')
        return redirect('/')
    return render_template("signup.html", message = error)

@app.route("/logout")
def logout():
    session.pop('username')
    return redirect('/')

if __name__ == "__main__":
    app.debug = True 
    app.run()