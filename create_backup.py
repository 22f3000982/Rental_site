#!/usr/bin/env python3
"""
Pre-deployment backup script
Run this before pushing to git or deploying to prevent data loss
"""

import sys
import os
import json
import sqlite3
from datetime import datetime

def create_backup():
    """Create a comprehensive backup of the database"""
    try:
        # Connect to the database
        db_path = 'instance/billing.db'
        if not os.path.exists(db_path):
            print("❌ Database file not found!")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        backup_data = {}
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📊 Found tables:", [table[0] for table in tables])
        
        # Backup each table
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_'):
                continue  # Skip SQLite internal tables
            
            print(f"🔄 Backing up table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            backup_data[table_name] = {
                'columns': column_names,
                'data': rows
            }
            
            print(f"✅ {table_name}: {len(rows)} records backed up")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'pre_deploy_backup_{timestamp}.json'
        
        # Save backup
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        # Also save as current backup
        with open('current_users_backup.json', 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        conn.close()
        
        print(f"🎉 Backup created successfully: {backup_filename}")
        print(f"📁 Also saved as: current_users_backup.json")
        
        # Show user statistics
        if 'user' in backup_data:
            total_users = len(backup_data['user']['data'])
            admin_count = sum(1 for row in backup_data['user']['data'] if row[5] == 1)  # is_admin column
            renter_count = total_users - admin_count
            print(f"👥 Users backed up: {total_users} (Admin: {admin_count}, Renters: {renter_count})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting pre-deployment backup...")
    print("=" * 50)
    
    # Change to backend directory if needed
    if os.path.exists('backend'):
        os.chdir('backend')
        print("📁 Changed to backend directory")
    
    success = create_backup()
    
    if success:
        print("=" * 50)
        print("✅ Backup completed successfully!")
        print("🔒 Your user data is now safe for deployment.")
        print("")
        print("Next steps:")
        print("1. Commit and push your code changes")
        print("2. Deploy to your hosting platform")
        print("3. The app will automatically restore data if needed")
    else:
        print("=" * 50)
        print("❌ Backup failed!")
        print("Please fix the issues before deploying.")
        sys.exit(1)
