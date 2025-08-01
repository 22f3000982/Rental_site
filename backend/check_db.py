import sqlite3
import os

db_path = 'instance/billing.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Current tables in database:')
    for table in tables:
        print(f'Table: {table[0]}')
    
    # Check users table if it exists
    if any('users' in str(table) for table in tables):
        cursor.execute('SELECT id, username, email, date_created FROM users')
        users = cursor.fetchall()
        print('\nCurrent users in database:')
        for user in users:
            print(f'ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Date: {user[3]}')
    else:
        print('\nNo users table found!')
    
    conn.close()
else:
    print(f'Database file {db_path} does not exist!')
