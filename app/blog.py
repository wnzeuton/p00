import sqlite3
from .config import DB_FILE

# Generates Blog HTML
def gen_html(title, author, page_category, description, page_id):
    post_html = f'''
        <div>
            <h2><a href="/blogs/{page_id}">{title}</a></h2>
            <p>Category: {page_category}</p>
            <p><a href = "/user/{author}">Created by {author}</a></p>
            <p>{description}</p>
        </div>
        '''
    return post_html

def fetch_blogs(categories_list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if categories_list is None:
        c.execute("SELECT title FROM categories")
        categories_list = [row[0] for row in c.fetchall()]
    c.execute('SELECT html FROM blogs')
    blogs_list = c.fetchall()
    conn.close()
    return blogs_list, categories_list

def insert_blog(form, session):
    title = form.get('title')
    description = form.get('description')
    blog_category = form.get('category')
    if title and description and blog_category:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        author_id = session['user'][0]
        try:
            c.execute("SELECT id FROM categories WHERE title = ?", (blog_category,))
            category_id = c.fetchone()
            if category_id:
                # Insert the blog into the database
                c.execute('SELECT MAX(id) FROM blogs')
                last_id = c.fetchone()[0] or 0
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