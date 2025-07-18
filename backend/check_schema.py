import sqlite3
import os

if os.path.exists('instance/readings.db'):
    conn = sqlite3.connect('instance/readings.db')
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(document)')
    columns = cursor.fetchall()
    print('Document table columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]}) - NOT NULL: {bool(col[3])} - Default: {col[4]}')
    
    # Get the CREATE statement
    cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="document"')
    result = cursor.fetchone()
    if result:
        print('\nDocument table CREATE statement:')
        print(result[0])
    conn.close()
else:
    print('Database file not found')
