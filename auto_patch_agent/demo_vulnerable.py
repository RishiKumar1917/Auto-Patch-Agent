import sqlite3
import os

def get_user_data(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    query = 'SELECT * FROM users WHERE username = ?'
    cursor.execute(query, (username,))
    
    return cursor.fetchall()

def authenticate_admin(password):
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if admin_password is None:
        raise ValueError("ADMIN_PASSWORD environment variable is not set")
    if password == admin_password:
        return True
    return False