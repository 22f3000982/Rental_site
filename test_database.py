#!/usr/bin/env python3
"""
Test Database Persistence
Run this script to verify that database initialization works correctly
"""

import sys
import os
sys.path.append('backend')

from app import app, db, create_admin_user, create_default_settings
from models import User

def test_database_initialization():
    """Test that database initializes correctly"""
    print("🧪 Testing Database Initialization")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create admin user
            create_admin_user()
            print("✅ Admin user creation tested")
            
            # Create default settings
            create_default_settings()
            print("✅ Default settings creation tested")
            
            # Verify admin user exists
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                print(f"✅ Admin user verified: {admin.email}")
            else:
                print("❌ Admin user not found!")
                return False
            
            # Count all users
            user_count = User.query.count()
            print(f"📊 Total users in database: {user_count}")
            
            print("\n🎉 Database initialization test PASSED!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization test FAILED: {e}")
            return False

if __name__ == "__main__":
    success = test_database_initialization()
    sys.exit(0 if success else 1)
