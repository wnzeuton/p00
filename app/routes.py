import sqlite3

from flask import render_template, request, session, redirect
from . import app
from .auth import sign_in_state, password_hash, get_user
from .blog import fetch_blogs, insert_blog
from .config import DB_FILE

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("index.html", guest=not sign_in_state(session),
                           username=session['user'][1] if sign_in_state(session) else "")

# BLOG PAGE (CONTAINS ALL POSTS)
@app.route("/blogs", methods=['GET', 'POST'])
def blog(categories_list=None):
    if request.method == 'POST':
        insert_blog(request.form, session)
    blogs_list, categories_list = fetch_blogs(categories_list)
    return render_template("all_blogs.html", guest=not sign_in_state(session), blogs=blogs_list, categories=categories_list)

@app.route("/blogs/<int:blog_id>")
def blog_detail(blog_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Fetch the specific blog post by ID
    c.execute("SELECT title, description, html FROM blogs WHERE id = ?", (blog_id,))
    blog_content = c.fetchone()
    conn.close()

    if blog_content:
        title, description, blog_description = blog_content
        return render_template("blog_post.html", title=title, description=description, content=blog_description)
    else:
        return render_template("404.html"), 404

# EDIT AND CREATE POSTS
@app.route("/edit")
def edit():
    return render_template("editpost.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    error = ""
    # If we're already logged in, just redirect to home page
    if sign_in_state(session):
        return redirect('/')
    email = request.form.get('email')
    if email:
        user = get_user("email", email.lower())
        if not user:
            return render_template("login.html", message="No such user with that email")
        if password_hash(request.form.get('password'), user[3])[0] != user[2]:
            return render_template("login.html", message="Incorrect password")
        session['user'] = user
        return redirect('/')
    return render_template("login.html", message=error)

@app.route("/logout")
def logout():
    if sign_in_state(session):
        session.pop('user')
    return redirect('/')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    error = []
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if len(password) < 10:
            error.append("Password must be at least 10 characters long")
        if password != confirm_password:
            error.append("Passwords do not match")
        if not error:
            pwd_salt = password_hash(password, "")
            new_user = (request.form.get('username'), pwd_salt[0], pwd_salt[1], request.form.get('email'))
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password, salt, email) VALUES (?, ?, ?, ?)", new_user)
                conn.commit()
                session['user'] = (c.lastrowid, new_user[0], new_user[1], new_user[2], new_user[3])
                return redirect('/')
            except sqlite3.IntegrityError:
                error.append("An account with that username or email already exists")
                conn.rollback()
            finally:
                c.close()
                conn.close()
    return render_template("signup.html", message=error)

@app.route("/user/<string:username>")
def user_profile(username):
    user = get_user("username", username)
    blogs, comments, owns_account = None, None, False
    if user:
        owns_account = sign_in_state(session) and username == session['user'][1]
    return render_template("user.html", owns_account=owns_account, user=user, blogs=blogs, comments=comments)

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    if not sign_in_state(session):
        return redirect('/')

    update = request.args.get('update') == 'true'
    req_type = request.args.get('type')
    error = []

    if update and request.method == 'POST' and req_type == 'password':
        current_password = request.form.get('password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user = session['user']
        if password_hash(current_password, user[3])[0] != user[2]:
            error.append("Incorrect current password")
        if len(new_password) < 10:
            error.append("New password must be at least 10 characters long")
        if new_password != confirm_password:
            error.append("New passwords do not match")

        if not error:
            pwd_salt = password_hash(new_password, "")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                c.execute("UPDATE users SET password = ?, salt = ? WHERE id = ?", (pwd_salt[0], pwd_salt[1], user[0]))
                conn.commit()
                session['user'] = (user[0], user[1], pwd_salt[0], pwd_salt[1], user[4])
                return redirect('/settings')
            except sqlite3.Error as e:
                error.append("An error occurred while updating the password")
                conn.rollback()
            finally:
                c.close()
                conn.close()
    return render_template("settings.html", username=session['user'][1], email=session['user'][4], update=update, type=req_type, message=error)
