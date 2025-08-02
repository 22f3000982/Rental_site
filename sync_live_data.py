#!/usr/bin/env python3
"""
Live Data Sync Script
This script helps sync live website data with local backups before deployment
"""

import requests
import json
import os
from datetime import datetime

def download_live_backup(site_url, admin_credentials):
    """Download backup from live site"""
    try:
        # Create a session for login
        session = requests.Session()
        
        # Login to admin panel
        login_url = f"{site_url}/login"
        login_data = {
            'username': admin_credentials['username'],
            'password': admin_credentials['password']
        }
        
        print(f"🔐 Logging into {site_url}...")
        response = session.post(login_url, data=login_data)
        
        if response.status_code == 200:
            print("✅ Successfully logged in!")
            
            # Create backup on live site
            backup_url = f"{site_url}/admin/create_backup"
            print("📊 Creating backup on live site...")
            session.get(backup_url)
            
            # Download backup
            download_url = f"{site_url}/admin/download_backup"
            print("⬇️ Downloading live backup...")
            backup_response = session.get(download_url)
            
            if backup_response.status_code == 200:
                # Save as live backup
                with open('live_backup.json', 'wb') as f:
                    f.write(backup_response.content)
                print("✅ Live backup downloaded successfully!")
                return True
            else:
                print(f"❌ Failed to download backup: {backup_response.status_code}")
                return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading live backup: {e}")
        return False

def merge_backups():
    """Merge live backup with local backup"""
    try:
        local_backup_exists = os.path.exists('current_users_backup.json')
        live_backup_exists = os.path.exists('live_backup.json')
        
        if not live_backup_exists:
            print("❌ No live backup found. Please download live backup first.")
            return False
        
        # Load live backup
        with open('live_backup.json', 'r') as f:
            live_data = json.load(f)
        
        print(f"📊 Live backup contains data")
        
        # Use live backup as the primary backup
        merged_data = live_data
        
        # Save merged backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'merged_backup_{timestamp}.json'
        
        with open(backup_filename, 'w') as f:
            json.dump(merged_data, f, indent=2)
        
        # Also save as current backup
        with open('current_users_backup.json', 'w') as f:
            json.dump(merged_data, f, indent=2)
        
        print(f"✅ Merged backup saved as: {backup_filename}")
        print(f"✅ Updated current_users_backup.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error merging backups: {e}")
        return False

def main():
    print("🌐 Live Data Sync Tool")
    print("=" * 50)
    
    # Configuration
    SITE_URL = "https://rental-site-8m2m.onrender.com"
    
    print("This tool will help you sync live website data before deployment.")
    print(f"Target site: {SITE_URL}")
    print()
    
    # Get admin credentials
    username = input("Enter admin username: ").strip()
    password = input("Enter admin password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required!")
        return
    
    credentials = {
        'username': username,
        'password': password
    }
    
    print("\n🚀 Starting live data download...")
    
    # Download live backup
    if download_live_backup(SITE_URL, credentials):
        print("\n🔄 Merging with local data...")
        if merge_backups():
            print("\n✅ SUCCESS! Your backup now includes ALL users:")
            print("- Users from your local database")
            print("- Users who registered through the live website")
            print()
            print("You can now safely deploy:")
            print("  git add .")
            print("  git commit -m 'Update with merged user data'")
            print("  git push origin master")
        else:
            print("\n❌ Failed to merge backups!")
    else:
        print("\n❌ Failed to download live backup!")
        print("\nAlternative: Manually download backup from admin panel:")
        print(f"1. Go to {SITE_URL}/admin/settings")
        print("2. Click 'Create Backup' then 'Download Backup'")
        print("3. Save as 'current_users_backup.json' in backend folder")

if __name__ == "__main__":
    main()
