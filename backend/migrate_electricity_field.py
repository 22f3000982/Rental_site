#!/usr/bin/env python3
"""
Migration script to add electricity_bill_required field to User table
"""

import sqlite3
import os
from app import app

def migrate_database():
    """Add electricity_bill_required column to User table"""
    db_path = os.path.join(app.instance_path, 'billing.db')
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'electricity_bill_required' not in columns:
            print("Adding electricity_bill_required column...")
            cursor.execute("ALTER TABLE user ADD COLUMN electricity_bill_required BOOLEAN DEFAULT 1")
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column already exists!")
        
        # Update existing users to have electricity_bill_required = True by default
        cursor.execute("UPDATE user SET electricity_bill_required = 1 WHERE electricity_bill_required IS NULL")
        conn.commit()
        
        # Verify the column was added
        cursor.execute("SELECT COUNT(*) FROM user WHERE electricity_bill_required IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"Updated {count} users with electricity_bill_required field")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = migrate_database()
        if success:
            print("Migration completed successfully!")
        else:
            print("Migration failed!")
