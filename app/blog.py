# Will Nzeuton, Tim Ng, Daniel Park, Yinwei Zhang
# Team lobo
# SoftDev
# p00 -- scenario 2
# 2024-11-07
import sqlite3
from .config import DB_FILE

def fetch_categories(categories_list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if categories_list is None:
        c.execute("SELECT title FROM categories")
        categories_list = [row[0] for row in c.fetchall()]
    conn.close()
    return categories_list

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
                    "INSERT INTO blogs (title, description, category_id, author_id) VALUES (?, ?, ?, ?)",
                    (title, description, category_id[0], author_id)
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error inserting blog: {e}")
            conn.rollback()
        finally:
            conn.close()

def delete_blogs(blog_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM blogs WHERE id = ?", (blog_id,))
    conn.commit()
    conn.close()