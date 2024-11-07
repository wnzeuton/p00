import sqlite3

from flask import render_template, request, session, redirect
from . import app
from .auth import sign_in_state, get_user
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
    categories_list = fetch_blogs(categories_list)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT * FROM blogs")

    blogs = c.fetchall()
    blogs_list = []
    for blog in blogs:
        author_id = blog[4]
        c.execute("SELECT username FROM users WHERE id = ?", (author_id,))
        result = c.fetchone()
        if not result:
            c.execute("DELETE FROM blogs WHERE author_id = ?", (author_id,))
            conn.commit()
            continue
        author_name = result[0]

        category_id = blog[3]
        c.execute("SELECT title FROM categories WHERE id = ?", (category_id,))
        result = c.fetchone()
        category_title = result[0]
        blogs_list.append([blog[0], blog[1], author_name, category_title, blog[2]])

    conn.close()
    return render_template("blogs/all_blogs.html", guest=not sign_in_state(session), blogs=blogs_list, categories=categories_list)

@app.route("/blogs/<int:blog_id>")
def blog_detail(blog_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Fetch the specific blog post by ID
    c.execute("SELECT title, description, author_id FROM blogs WHERE id = ?", (blog_id,))
    blog_content = c.fetchone()
    c.execute("SELECT username FROM users WHERE id = ?", (blog_content[2],))
    author_username = c.fetchone()
    c.execute("SELECT * FROM posts WHERE blog_id=?",(blog_id,))
    entries = c.fetchall()
    conn.close()
    is_owner = (sign_in_state(session) and author_username[0] == session['user'][1])
    if blog_content:
        title, description, author_id = blog_content
        return render_template("blogs/blog_post.html", is_owner = is_owner, title=title, description=description, author = author_username[0], blog_id=blog_id, entries = entries)
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
        return render_template("blogs/create_entry.html", blog_id = blog_id)
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
    return render_template('blogs/entry.html', entry_title = entry_title, entry_author = entry_author, entry_date = entry_date, blog_id = blog_id, blog_name = blog_name, entry_content = entry_content)

# EDIT AND CREATE POSTS
@app.route("/edit")
def edit():
    return render_template("blogs/editpost.html")

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
    return render_template("blogs/category.html", categories=categories, blogs=blogs, selected_category=selected_category)