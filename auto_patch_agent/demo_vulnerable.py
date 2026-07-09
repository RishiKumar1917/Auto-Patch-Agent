import sqlite3

def get_user_data(username):
    # SECURITY VULNERABILITY: SQL Injection
    # Using string formatting for SQL queries allows attackers to bypass authentication or extract data.
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    return cursor.fetchall()

def authenticate_admin(password):
    # SECURITY VULNERABILITY: Hardcoded sensitive credentials
    # Storing credentials in plain text is insecure.
    ADMIN_PASSWORD = "SuperSecretAdminPassword123!"
    if password == ADMIN_PASSWORD:
        return True
    return False
