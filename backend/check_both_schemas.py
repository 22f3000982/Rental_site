import sqlite3
import os

for db_file in ['instance/readings.db', 'instance/billing.db']:
    if os.path.exists(db_file):
        print(f'\n=== Checking {db_file} ===')
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if document table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document'")
        if cursor.fetchone():
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
        else:
            print('Document table does not exist')
        
        conn.close()
    else:
        print(f'{db_file} not found')
