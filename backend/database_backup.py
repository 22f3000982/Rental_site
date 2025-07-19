#!/usr/bin/env python3
"""
Database Backup and Restore Utility
This script helps backup and restore user data to prevent loss during deployments
"""

import sqlite3
import json
import os
from datetime import datetime

def backup_database(db_path='instance/readings.db', backup_file=None):
    """Backup all users and critical data from SQLite database"""
    
    if backup_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'database_backup_{timestamp}.json'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        backup_data = {}
        
        # Backup users
        cursor.execute('SELECT * FROM user')
        users = cursor.fetchall()
        cursor.execute('PRAGMA table_info(user)')
        user_columns = [column[1] for column in cursor.fetchall()]
        backup_data['users'] = {
            'columns': user_columns,
            'data': users
        }
        
        # Backup system settings
        try:
            cursor.execute('SELECT * FROM system_settings')
            settings = cursor.fetchall()
            cursor.execute('PRAGMA table_info(system_settings)')
            settings_columns = [column[1] for column in cursor.fetchall()]
            backup_data['settings'] = {
                'columns': settings_columns,
                'data': settings
            }
        except sqlite3.OperationalError:
            backup_data['settings'] = None
        
        # Backup meter readings (optional - can be large)
        try:
            cursor.execute('SELECT COUNT(*) FROM meter_reading')
            reading_count = cursor.fetchone()[0]
            if reading_count < 1000:  # Only backup if less than 1000 readings
                cursor.execute('SELECT * FROM meter_reading')
                readings = cursor.fetchall()
                cursor.execute('PRAGMA table_info(meter_reading)')
                reading_columns = [column[1] for column in cursor.fetchall()]
                backup_data['meter_readings'] = {
                    'columns': reading_columns,
                    'data': readings
                }
            else:
                backup_data['meter_readings'] = {'note': 'Too many readings, skipped backup'}
        except sqlite3.OperationalError:
            backup_data['meter_readings'] = None
        
        conn.close()
        
        # Save backup to JSON file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"Database backup saved to: {backup_file}")
        print(f"Users backed up: {len(users)}")
        return True
        
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def restore_database(backup_file, db_path='instance/readings.db'):
    """Restore users and critical data from backup file"""
    
    if not os.path.exists(backup_file):
        print(f"Backup file {backup_file} not found!")
        return False
    
    try:
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Restore users
        if 'users' in backup_data and backup_data['users']:
            users_data = backup_data['users']
            columns = users_data['columns']
            placeholders = ', '.join(['?' for _ in columns])
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    password_plain VARCHAR(255),
                    room_number VARCHAR(20),
                    phone_number VARCHAR(20),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_approved BOOLEAN DEFAULT FALSE,
                    date_registered DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            for user_data in users_data['data']:
                try:
                    cursor.execute(f'INSERT INTO user ({", ".join(columns)}) VALUES ({placeholders})', user_data)
                except sqlite3.IntegrityError as e:
                    print(f"User already exists, skipping: {user_data[1] if len(user_data) > 1 else 'unknown'}")
        
        # Restore system settings
        if 'settings' in backup_data and backup_data['settings']:
            settings_data = backup_data['settings']
            columns = settings_data['columns']
            placeholders = ', '.join(['?' for _ in columns])
            
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    electricity_rate DECIMAL(10,2) DEFAULT 5.00,
                    rent_amount DECIMAL(10,2) DEFAULT 5000.00,
                    maintenance_charge DECIMAL(10,2) DEFAULT 500.00
                )
            ''')
            
            for setting_data in settings_data['data']:
                try:
                    cursor.execute(f'INSERT INTO system_settings ({", ".join(columns)}) VALUES ({placeholders})', setting_data)
                except sqlite3.IntegrityError:
                    print("Settings already exist, skipping")
        
        conn.commit()
        conn.close()
        
        print(f"Database restored from: {backup_file}")
        return True
        
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python database_backup.py backup [backup_file]")
        print("  python database_backup.py restore <backup_file>")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == 'backup':
        backup_file = sys.argv[2] if len(sys.argv) > 2 else None
        backup_database(backup_file=backup_file)
    
    elif action == 'restore':
        if len(sys.argv) < 3:
            print("Please specify backup file to restore from")
            sys.exit(1)
        backup_file = sys.argv[2]
        restore_database(backup_file)
    
    else:
        print("Invalid action. Use 'backup' or 'restore'")
