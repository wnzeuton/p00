import sqlite3

from flask import render_template, request, session, redirect
from . import app
from .auth import sign_in_state, password_hash, get_user, valid_username
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
    c.execute("SELECT title, description, html, author_id FROM blogs WHERE id = ?", (blog_id,))
    blog_content = c.fetchone()
    c.execute("SELECT username FROM users WHERE id = ?", (blog_content[3],))
    author_username = c.fetchone()
    c.execute("SELECT * FROM posts WHERE blog_id=?",(blog_id,))
    entries = c.fetchall()
    conn.close()
    is_owner = (sign_in_state(session) and author_username[0] == session['user'][1])

    if blog_content:
        title, description, blog_description, author_id = blog_content
        return render_template("blog_post.html", is_owner = is_owner, title=title, description=description, content=blog_description, author = author_username[0], blog_id=blog_id, entries = entries)
    else:
        return render_template("404.html"), 404
@app.route("/blogs/<int:blog_id>/create", methods=['GET', 'POST'])
def create_entry(blog_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT author_id FROM blogs WHERE id = ?", (blog_id,))
    author_id = c.fetchone()[0]
    conn.close()
    if not sign_in_state(session) or author_id != session['user'][0]:
        return redirect('/')
    if not request.form:
        return render_template("create_entry.html", blog_id = blog_id)
    entry_title = request.form.get('title')
    entry_content = request.form.get('content')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO posts (title, author_id, blog_id, content) VALUES (?, ?, ?, ?)", (entry_title, author_id, blog_id, entry_content.replace('\n', "<br>")))
    conn.commit()
    conn.close()
    print("inserted post")
    return redirect(f'/blogs/{blog_id}')
@app.route("/blogs/<int:blog_id>/<int:entry_id>")
def view_entry(blog_id, entry_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, date, author_id, content FROM posts WHERE id = ?", (entry_id,))
    entry = c.fetchone()
    if entry:
        entry_title, entry_date, entry_author, entry_content = entry
    else:
        return redirect(f'/blogs/{blog_id}')
    entry_author = get_user("id", entry_author)[1]
    c.execute("SELECT title FROM blogs WHERE id =?", (blog_id,))
    blog_name = c.fetchone()[0]
    conn.close()
    return render_template('entry.html', entry_title = entry_title, entry_author = entry_author, entry_date = entry_date, blog_id = blog_id, blog_name = blog_name, entry_content = entry_content)
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
        if not valid_username(request.form.get('username')):
            error.append("Username shouldn't contain spaces or special characters")
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
    blogs = None
    comments = None
    owns_account = False
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if user is not None:
            user_id = user[0] 
            if sign_in_state(session) and username == session['user'][1]:
               owns_account = True
            c.execute('''
                SELECT * FROM blogs WHERE author_id = ?
            ''', (user_id,))
            blogs = c.fetchall()
            for i in range(len(blogs)):
                cat_id = blogs[i][3]
                c.execute("SELECT title FROM categories WHERE id = ?", (cat_id,))
                cat_title = c.fetchone()
                usr_blog = (blogs[i][0], blogs[i][1], blogs[i][2], cat_title[0], username, blogs[i][5])
                blogs[i] = usr_blog
                
            c.execute('''
                SELECT * FROM comments WHERE author_id = ?
            ''', (user_id,))
            comments = c.fetchall()

    except sqlite3.Error as e:
        conn.rollback()
        print(e)
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        c.close()
        conn.close()
    return render_template("user.html", owns_account = owns_account, user = user, blogs = blogs, comments = comments)

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    if not sign_in_state(session):
        return redirect('/')

    update = request.args.get('update') == 'true'
    req_type = request.args.get('type')
    valid_types = ['username', 'email', 'password']
    if req_type not in valid_types and request.args:
        return redirect('/settings')
    if update and request.form.get(req_type) is not None:
        form_info = request.form.get(req_type)
        form_info2 = None
        if req_type == 'password':
            form_info = request.form.get('new_password')
            form_info2 = request.form.get('confirm_password')
        print("Updating " + req_type + " to " + form_info)

        error = []
        if (password_hash(request.form.get('password'), session['user'][3])[0]) != session['user'][2]:
            error.append("Incorrect password")
        if form_info2 is not None and form_info2 != form_info:
            error.append("New passwords do not match")
        if form_info2 is not None and len(request.form.get('new_password')) < 10:
            error.append("Password must be at least 10 characters long")
        if len(error) != 0:
            return render_template("settings.html", update=update, type=req_type, username=session['user'][1],
                                   email=session['user'][4], message=error)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            if req_type != 'password':
                c.execute(f'''
                            UPDATE users
                            SET {req_type} = ?
                            WHERE id = ?
                        ''', (form_info, session['user'][0]))
            else:
                pwd = password_hash(form_info, "")
                c.execute(f'''
                            UPDATE users
                            SET {req_type} = ?, salt = ?
                            WHERE id = ?
                        ''', (pwd[0], pwd[1], session['user'][0]))
            print("attempting break through")
        except sqlite3.IntegrityError:
            error.append(f"An account with that {req_type} already exists")
            print("already exists")
            conn.rollback()
        except sqlite3.Error as e:
            error.append(f"ERROR: {e} - CONTACT DEVELOPERS FOR HELP")
            print(e)
            conn.rollback()
        except Exception as e:
            error.append(str(e))
            conn.rollback()
            print(e)
        finally:
            if len(error) == 0:
                if req_type == 'username' and any(
                        c in " `~!@#$%^&*()=+[]{\}\|,./<>?;\':\"" for c in request.form.get('username')):
                    error.append("Username shouldn't contain spaces or special characters")
            if len(error) != 0:
                conn.rollback()
            else:
                conn.commit()
                c.execute("SELECT * FROM users WHERE id = ?", (session['user'][0],))
                result = c.fetchone()
                session['user'] = result
                print("Successful!")
                return render_template('settings.html', update=False, type=None, username=session['user'][1],
                                       email=session['user'][4], message=[f"Updated {req_type}!"])
            c.close()
            conn.close()
            return render_template("settings.html", update=update, type=req_type, username=session['user'][1],
                                   email=session['user'][4], message=error)
    return render_template("settings.html", update=update, type=req_type, username=session['user'][1],
                           email=session['user'][4])


@app.route("/category", methods=['GET', 'POST'])
def category():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT title FROM categories")
    categories = [row[0] for row in c.fetchall()]
    selected_category = request.form.get("category") or "Art/Music"
    print(selected_category)
    c.execute('''
        SELECT blog.id, blog.title, blog.description, user.username
        FROM blogs blog
        JOIN categories c ON blog.category_id = c.id
        JOIN users user ON blog.author_id = user.id
        WHERE c.title = ?
    ''', (selected_category,))
    blogs = c.fetchall()
    conn.close()
    return render_template("category.html", categories=categories, blogs=blogs, selected_category=selected_category)