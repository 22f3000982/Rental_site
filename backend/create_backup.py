#!/usr/bin/env python3
"""
Create a backup of current registered users before deployment
Run this before pushing to GitHub to preserve user data
"""

import sys
import os
sys.path.append('.')

def create_current_backup():
    """Create a backup of current users"""
    try:
        from app import app, db, User, RentPayment, ElectricityBill
        
        with app.app_context():
            # Get all non-admin users
            users = User.query.filter_by(is_admin=False).all()
            
            if not users:
                print("No renter users found to backup")
                return
            
            backup_data = {
                'users': [],
                'backup_timestamp': str(datetime.now()),
                'user_count': len(users)
            }
            
            for user in users:
                user_data = {
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'room_number': user.room_number,
                    'is_admin': user.is_admin,
                    'is_active': user.is_active,
                    'created_at': str(user.created_at) if hasattr(user, 'created_at') else None
                }
                backup_data['users'].append(user_data)
            
            # Save backup
            import json
            with open('current_users_backup.json', 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Successfully backed up {len(users)} users to 'current_users_backup.json'")
            print("You can now safely deploy to Render!")
            
    except Exception as e:
        print(f"❌ Error creating backup: {e}")

if __name__ == "__main__":
    from datetime import datetime
    create_current_backup()
