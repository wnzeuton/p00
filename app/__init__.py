import os
import sqlite3
from flask import Flask, render_template, request, session, redirect
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(32)
DB_FILE = os.path.join(os.path.dirname(__file__), "xase.db")


# CHECK IF A USER IS SIGNED IN
def sign_in_state():
    # note that session['user'] is a TUPLE in the shape of the table row: (id, normalized_username, username, password, salt, email)
    return 'user' in session.keys() and session['user'] is not None


# PASSWORD ENCRYPTION
def password_hash(password, salt):
    if salt == "":
        salt = bcrypt.gensalt()
    return [bcrypt.hashpw(password.encode('utf-8'), salt), salt]


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("index.html", guest=not sign_in_state(),
                           username=session['user'][1] if sign_in_state() else "")

# Generates Blog HTML
def gen_html(title, author, page_category, description, page_id):
    post_html = f'''
        <div>
            <h2><a href="/blogs/{page_id}">{title}</a></h2>
            <p>Category: {page_category}</p>
            <p>Created by {author}</p>
            <div>{description}</div>
        </div>
        '''
    return post_html


# BLOG PAGE (CONTAINS ALL POSTS)
@app.route("/blogs", methods=['GET', 'POST'])
def blog(categories_list=None):
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        blog_category = request.form.get('category')

        if title and description and blog_category:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            author_id = session['user'][0]

            # Get category ID from the category name
            c.execute("SELECT id FROM categories WHERE title = ?", (blog_category,))
            category_id = c.fetchone()

            if category_id:
                # Insert the blog into the database
                try:
                    c.execute('SELECT MAX(id) FROM blogs')
                    last_id = c.fetchone()[0]
                    c.execute(
                        "INSERT INTO blogs (title, description, category_id, author_id, html) VALUES (?, ?, ?, ?, ?)",
                        (title, description, category_id[0], author_id,
                         gen_html(title, session['user'][1], blog_category, description, last_id + 1))
                    )
                    conn.commit()
                except sqlite3.Error as e:
                    print(f"Error inserting blog: {e}")
                    conn.rollback()
                finally:
                    conn.close()
            else:
                print("Category not found")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if categories_list is None:
        c.execute("SELECT title FROM categories")
        categories_list = [row[0] for row in c.fetchall()]

    c.execute('SELECT html FROM blogs')
    blogs_list = c.fetchall()

    conn.close()
    return render_template("blogpost.html", guest=not sign_in_state(), blogs=blogs_list, categories=categories_list)


@app.route("/blog/<int:blog_id>")
def blog_detail(blog_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Fetch the specific blog post by ID
    c.execute("SELECT title, description, html FROM blogs WHERE id = ?", (blog_id,))
    blog_content = c.fetchone()
    conn.close()

    if blog_content:
        title, description, html_content = blog_content
        return render_template("blog_detail.html", title=title, description=description, content=html_content)
    else:
        # If the blog post is not found, show a 404 page
        return render_template("404.html"), 404


# EDIT AND CREATE POSTS
@app.route("/edit")
def edit():
    return render_template("editpost.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    error = ""
    # If we're already logged in, just redirect to home page
    if sign_in_state():
        return redirect('/')
    email = (request.form.get('email'))
    if email is not None:
        conn = sqlite3.connect('xase.db')
        c = conn.cursor()
        try:
            c.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
            authed_user = c.fetchone()
        except sqlite3.Error as e:
            e
        finally:
            c.close()
            conn.close()
        if authed_user is None:
            return render_template("login.html", message='No such user with that email')
        if password_hash(request.form.get('password'), authed_user[3])[0] != authed_user[2]:
            return render_template("login.html", message="Incorrect password")
        session['user'] = authed_user
        return redirect('/')
    return render_template("login.html", message=error)


@app.route("/user")
def user():
    return render_template("user.html")


@app.route("/category")
def category(categories_list=None):
    return render_template("category.html", categories=categories_list)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    error = []
    if len(request.form) != 0:
        pwd_salt = password_hash(request.form.get('password'), "")
        new_user = (request.form.get('username'), pwd_salt[0], pwd_salt[1], request.form.get('email'))
        conn = sqlite3.connect('xase.db')
        c = conn.cursor()
        try:
            c.execute('''
            INSERT INTO users (username, password, salt, email) VALUES (?, ?, ?, ?)
            ''', new_user)
        except sqlite3.IntegrityError:
            error.append("An account with that username or email already exists")
            conn.rollback()
        except sqlite3.Error as e:
            error.append(f"ERROR: {e} - CONTACT DEVELOPERS FOR HELP")
            conn.rollback()
        except Exception as e:
            error.append(str(e))
            conn.rollback()
        finally:
            if len(error) == 0:
                if any(c in " `~!@#$%^&*()=+[]\{\}\|,./<>?;\':\"" for c in request.form.get('username')):
                    error.append("Username shouldn't contain spaces or special characters")
                if len(request.form.get('password')) < 10:
                    error.append("Password must be at least 10 characters long")
                if request.form.get('password') != request.form.get('confirm_password'):
                    error.append("Passwords do not match")
            if len(error) != 0:
                conn.rollback()
            else:
                conn.commit()
                session['user'] = (c.lastrowid, new_user[0], new_user[1], new_user[2], new_user[3])
            c.close()
            conn.close()
    if len(error) == 0 and len(request.form) != 0:
        return redirect('/')
    if len(request.form) == 0:
        error = []
    return render_template("signup.html", message=error)


@app.route("/logout")
def logout():
    if sign_in_state():
        session.pop('user')
    return redirect('/')


@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if not sign_in_state():
        return redirect('/')
    update = (request.args.get('update') == 'true')
    req_type = request.args.get('type')

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
            return render_template("profile.html", update=update, type=req_type, username=session['user'][1],
                                   email=session['user'][4], message=error)
        conn = sqlite3.connect('xase.db')
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
                c.execute("SELECT * FROM users WHERE id = ?", str(session['user'][0]))
                result = c.fetchone()
                session['user'] = result
                print("Successful!")
                return render_template('profile.html', update=False, type=None, username=session['user'][1],
                                       email=session['user'][4], message=[f"Updated {req_type}!"])
            c.close()
            conn.close()
            return render_template("profile.html", update=update, type=req_type, username=session['user'][1],
                                   email=session['user'][4], message=error)
    return render_template("profile.html", update=update, type=req_type, username=session['user'][1],
                           email=session['user'][4])


if __name__ == "__main__":
    app.debug = True
    app.run()
