# DATA TABLE

import sqlite3, csv

DB_FILE = "xase.db"

db = sqlite3.connect(DB_FILE)
c = db.cursor()

# CREATING DATA TABLES

# USER TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT UNIQUE,
    email TEXT UNIQUE
);
''')

# CATEGORIES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    title TEXT UNIQUE
);
''')

# POSTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    title TEXT UNIQUE,
    date
);
''')

# COMMENTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER
);
''')

db.commit()
db.close()


import os
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = os.urandom(32)

@app.route("/")
def disp_loginpage():
    return render_template("index.html")

@app.route("/blog")
def response():
    return render_template("blogpost.html")

@app.route("/edit")
def response():
    return render_template("editpost.html")

@app.route("/login")
def response():
    return render_template("login.html")

@app.route("/user")
def response():
    return render_template("user.html")

@app.route("/category")
def response():
    return render_template("category.html")

@app.route("/signup")
def response():
    return render_template("signup.html")

@app.route("/logout")
def disp_logoutpage():
    return render_template('logout.html')

if __name__ == "__main__":
    app.debug = True 
    app.run()