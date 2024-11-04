import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "xase.db")

def clear_database(DB_FILE):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    tables = ['users', 'categories', 'posts', 'comments', 'blogs']
    try:
        for table in tables:
            c.execute(f'DELETE FROM {table};')
            c.execute(f'DELETE FROM sqlite_sequence WHERE name="{table}";') 
        conn.commit()
        print("All data cleared successfully.")
    except sqlite3.Error as e:
        print(f"ERROR: {e}")
    finally:
        c.close()
        conn.close()

clear_database()