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
from flask import Flask, render_template, request, session

app = Flask(__name__)

@app.route("/")
def disp_loginpage():
    return render_template("index.html")

@app.route("/blog")
def blog():
    return render_template("blogpost.html")

@app.route("/edit")
def edit():
    return render_template("editpost.html")

@app.route("/login")
def login():
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
def disp_logoutpage():
    return render_template('logout.html')

if __name__ == "__main__":
    app.debug = True 
    app.run()