import bcrypt

# DATA TABLE

import sqlite3, csv

DB_FILE = "xase.db"

db = sqlite3.connect(DB_FILE)
c = db.cursor()

# CREATING DATA TABLES

# USER TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE
);
''')

#BLOG Table
c.execute('''
CREATE TABLE IF NOT EXISTS blogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    author_id INTEGER,
    html TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);
''')

# CATEGORIES TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE COLLATE NOCASE
);
''')

# POSTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date DATE DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER,
    blog_id INTEGER,
    content TEXT,
    FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);
''')

# COMMENTS TABLE
c.execute('''
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    date DATE DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER,
    post_id INTEGER,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);
''')


categories_list = [
    "Art/Music",
    "Technology",
    "Science",
    "Health",
    "Travel",
    "Food",
    "Lifestyle",
    "Education",
    "Finance",
    "Sports",
    "Fashion",
    "Business",
    "Politics",
    "Environment",
    "History",
    "Other"
]

for category in categories_list:
    try:
        c.execute("INSERT INTO categories (title) VALUES (?)", (category,))
    except sqlite3.IntegrityError:
        print(f"Category '{category}' already exists in the database.")

db.commit()
db.close()


import os
from flask import Flask, render_template, request, session, redirect

app = Flask(__name__)
app.secret_key = os.urandom(32)

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
def blog():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        print(title, description, category)

        if title and description and category:
            conn = sqlite3.connect('xase.db')
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

    conn = sqlite3.connect('xase.db')
    c = conn.cursor()
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
        if(password_hash(request.form.get('password'), user[3])[0] != user[2]):
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
    return render_template("category.html", categories = categories_list)

@app.route("/signup", methods = ['GET', 'POST'])
def signup():
    error = []
    if(len(request.form) != 0):
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
            if(len(error) == 0):
                if any(c in " `~!@#$%^&*()=+[]{}|,./<>?;':\"" for c in request.form.get('username')):
                    error.append("Username shouldn't contain spaces or special characters")
                if(len(request.form.get('password')) < 10):
                    error.append("Password must be at least 10 characters long")
                if(request.form.get('password') != request.form.get('confirm_password')):
                    error.append("Passwords do not match")
            if(len(error)!=0):
                conn.rollback()
            else:
                conn.commit()
                session['user'] = (c.lastrowid, new_user[0], new_user[1], new_user[2], new_user[3])
            c.close()
            conn.close()
    if(len(error) == 0 and len(request.form) != 0):
        return redirect('/')
    if(len(request.form) == 0):
        error = []
    return render_template("signup.html", message = error)

@app.route("/logout")
def logout():
    if(sign_in_state()):
        session.pop('user')
    return redirect('/')

@app.route("/profile", methods = ['GET', 'POST'])
def profile():
    if(not sign_in_state()):
        return redirect('/')
    update = (request.args.get('update') == 'true')
    type = request.args.get('type')
    
    if(update and request.form.get(type) != None):
        formInfo = request.form.get(type)
        formInfo2 = None
        if(type == 'password'):
            formInfo = request.form.get('new_password')
            formInfo2 = request.form.get('confirm_password')
        print("Updating " + type + " to " + formInfo)
        
        error = []
        if(password_hash(request.form.get('password'), session['user'][3])[0]) != session['user'][2]:
            error.append("Incorrect password")
        if(formInfo2 != None and formInfo2 != formInfo):
            error.append("New passwords do not match")
        if(formInfo2 != None and len(request.form.get('new_password')) < 10):
            error.append("Password must be at least 10 characters long")
        if(len(error) != 0):
            return render_template("profile.html", update = update, type = type, username = session['user'][1], email = session['user'][4], message = error)
        conn = sqlite3.connect('xase.db')
        c = conn.cursor()
        try:
            if(type != 'password'):
                c.execute(f'''
                            UPDATE users
                            SET {type} = ?
                            WHERE id = ?
                        ''', (formInfo, session['user'][0]))
            else:
                pwd = password_hash(formInfo, "")
                c.execute(f'''
                            UPDATE users
                            SET {type} = ?, salt = ?
                            WHERE id = ?
                        ''', (pwd[0], pwd[1], session['user'][0]))
            print("attempting break through")
        except sqlite3.IntegrityError:
            error.append(f"An account with that {type} already exists")
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
            if(len(error) == 0):
                if (type == 'username' and any(c in " `~!@#$%^&*()=+[]{}|,./<>?;':\"" for c in request.form.get('username'))):
                    error.append("Username shouldn't contain spaces or special characters")
            if(len(error)!=0):
                conn.rollback()
            else:
                conn.commit()
                c.execute("SELECT * FROM users WHERE id = ?", str(session['user'][0]))
                result = c.fetchone()
                session['user'] = result
                print("Successful!")
                return render_template('profile.html', update=False,type=None,username=session['user'][1], email=session['user'][4], message = [f"Updated {type}!"])
            c.close()
            conn.close()
            return render_template("profile.html", update = update, type = type, username = session['user'][1], email = session['user'][4], message = error)
    return render_template("profile.html", update = update, type = type, username = session['user'][1], email = session['user'][4])
   
if __name__ == "__main__":
    app.debug = True 
    app.run()