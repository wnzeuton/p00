import bcrypt
import sqlite3
from .config import DB_FILE

# CHECK IF A USER IS SIGNED IN
def sign_in_state(session):
    # note that session['user'] is a TUPLE in the shape of the table row: (id, normalized_username, username, password, salt, email)
    return 'user' in session.keys() and session['user'] is not None

def get_user(column, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        query = f"SELECT * FROM users WHERE {column} = ?"
        c.execute(query, (value,))
        user = c.fetchone()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        user = None
    finally:
        c.close()
        conn.close()
    return user

# PASSWORD ENCRYPTION
def password_hash(password, salt):
    if salt == "":
        salt = bcrypt.gensalt()
    return [bcrypt.hashpw(password.encode('utf-8'), salt), salt]

def valid_username(username):
    return not any(c in ' ~!@#$%^&*()`\\\'\";:[]{«‘“}|,<>/?' for c in username)
