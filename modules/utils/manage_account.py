from flaskapi.extensions import mysql
from modules.utils.logger import log_user_action

def fetch_all_users():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, email, fullname, dob, phone, address, is_locked, created_at, failed_attempts, last_failed_login
        FROM users
        WHERE fullname != 'Administrator' 
        ORDER BY created_at DESC
    """)
    users = cur.fetchall()
    cur.close()
    return users

def toggle_user_lock(email, lock: bool):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE users SET is_locked = %s WHERE email = %s
    """, (lock, email))
    mysql.connection.commit()
    log_user_action(
        email, "Lock Account" if lock else "Unlock Account", "Success")
    cur.close()