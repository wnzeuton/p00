import os
import sqlite3
from flask import Flask, render_template, request, session, redirect
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(32)
DB_FILE = os.path.join(os.path.dirname(__file__), "xase.db")

#CHECK IF A USER IS SIGNED IN
def sign_in_state():
    #note that session['user'] is a TUPLE in the shape of the table row: (id, normalized_username, username, password, salt, email)
    return 'user' in session.keys() and session['user'] != None

#PASSWORD ENCRYPTION
def password_hash(password, salt):
    if(salt == ""):
        salt = bcrypt.gensalt()
    return [bcrypt.hashpw(password.encode('utf-8'), salt), salt]


@app.route("/", methods = ['GET', 'POST'])
def home():
    return render_template("index.html", guest = not sign_in_state(), username = session['user'][1] if sign_in_state() else "")

# Generates Blog HTML
def gen_html(title, author, category, description):
    post_html = f'''
        <div>
            <h2>{title}</h2>
            <p>Category: {category}</p>
            <p>Created by {author}</p>
            <div>{description}</div>
        </div>
        '''
    return post_html

#BLOG PAGE (CONTAINS ALL POSTS)
@app.route("/blogs", methods=['GET', 'POST'])
def blog(categories_list=None):
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        print(title, description, category)

        if title and description and category:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            author_id = session['user'][0]

            # Get category ID from the category name
            c.execute("SELECT id FROM categories WHERE title = ?", (category,))
            category_id = c.fetchone()

            if category_id:
                # Insert the blog into the database
                try:
                    c.execute(
                        "INSERT INTO blogs (title, description, category_id, author_id, html) VALUES (?, ?, ?, ?, ?)",
                        (title, description, category_id[0], author_id, gen_html(title, session['user'][1], category, description))
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
    return render_template("blogpost.html", guest = not sign_in_state(), blogs = blogs_list, categories = categories_list)

#EDIT AND CREATE POSTS
@app.route("/edit")
def edit():
    return render_template("editpost.html")


@app.route("/login", methods = ['GET', 'POST'])
def login():
    error = ""
    #If we're already logged in, just redirect to home page
    if sign_in_state():
        return redirect('/')
    email = (request.form.get('email'))
    if email is not None:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
            user = c.fetchone()
        except sqlite3.Error as e:
            error = e
        finally:
            c.close()
            conn.close()
        if user and password_hash(request.form.get('password'), user[3])[0] == user[2]:
            session['user'] = user
            return redirect('/')
    return render_template("login.html", message=error)

@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/category")
def category(categories_list=None):
    return render_template("category.html", categories = categories_list)

@app.route("/signup", methods = ['GET', 'POST'])
def signup():
    error = []
    if request.form:
        pwd_salt = password_hash(request.form.get('password'), "")
        new_user = (request.form.get('username'), pwd_salt[0], pwd_salt[1], request.form.get('email'))
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, salt, email) VALUES (?, ?, ?, ?)', new_user)
        except sqlite3.IntegrityError:
            error.append("An account with that username or email already exists")
            conn.rollback()
        finally:
            if not error:
                conn.commit()
                session['user'] = (c.lastrowid, new_user[0], new_user[1], new_user[2], new_user[3])
            c.close()
            conn.close()
    return render_template("signup.html", message = error)

@app.route("/logout")
def logout():
    if sign_in_state():
        session.pop('user')
    return redirect('/')

@app.route("/profile", methods = ['GET', 'POST'])
def profile():
    if not sign_in_state():
        return redirect('/')
    return render_template("profile.html", username=session['user'][1], email=session['user'][4])
if __name__ == "__main__":
    app.debug = True
    app.run()