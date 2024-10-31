# DATA TABLE

import sqlite3, csv

DB_FILE = "xase.db"

db = sqlite3.connect(DB_FILE)
c = db.cursor()

# CREATING DATA TABLES

# USER TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT UNIQUE,
    email TEXT UNIQUE
);
''')

# CATEGORIES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    title TEXT UNIQUE
);
''')

# POSTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    title TEXT UNIQUE,
    date DATE,
    category INTEGER,
    username TEXT,
    content TEXT
);
''')

# COMMENTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY,
    content TEXT,
    date DATE,
    username TEXT,
    post_id INTEGER
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

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop('username')
    return redirect('/')

if __name__ == "__main__":
    app.debug = True 
    app.run()