#!/usr/bin/env python3
"""
Deployment Script for Rental Management System
This script ensures database persistence across deployments
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(command, description):
    """Run a command and print the result"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} failed")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False

def backup_before_deploy():
    """Create backup before deployment"""
    print("\n" + "="*60)
    print("🔄 PRE-DEPLOYMENT BACKUP")
    print("="*60)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"pre_deploy_backup_{timestamp}.json"
    
    if os.path.exists('backend/instance/readings.db'):
        if run_command(f'cd backend && python database_backup.py backup {backup_file}', 
                      f"Backing up database to {backup_file}"):
            print(f"✅ Database backup saved: backend/{backup_file}")
            return f"backend/{backup_file}"
    else:
        print("⚠️  No existing database found - this might be first deployment")
    
    return None

def deploy_to_github():
    """Deploy changes to GitHub"""
    print("\n" + "="*60)
    print("🚀 GITHUB DEPLOYMENT")
    print("="*60)
    
    # Add all changes
    if not run_command('git add .', "Adding all changes"):
        return False
    
    # Commit changes
    commit_message = f"Deploy with database persistence - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("⚠️  No changes to commit or commit failed")
    
    # Push to GitHub
    if not run_command('git push origin master', "Pushing to GitHub"):
        return False
    
    print("✅ Successfully deployed to GitHub!")
    return True

def post_deploy_setup():
    """Instructions for post-deployment setup"""
    print("\n" + "="*60)
    print("📋 POST-DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    
    print("""
After your app is deployed, follow these steps:

1. 🌐 ACCESS YOUR DEPLOYED APP
   - Go to your deployed app URL
   - The database will be automatically initialized

2. 🔑 LOGIN AS ADMIN
   - Email: ashraj77777@gmail.com
   - Password: 4129
   
3. 📊 VERIFY DATA PERSISTENCE
   - Check if admin user exists
   - Register a test user
   - Verify the user persists after app restart

4. 🔄 RESTORE BACKUP (if needed)
   - Upload backup file to your server
   - Run: python database_backup.py restore <backup_file>

5. 🔧 PRODUCTION DATABASE (Recommended)
   - For Railway: Use PostgreSQL add-on
   - For Heroku: Use Heroku Postgres
   - Update DATABASE_URL in environment variables
""")

def main():
    """Main deployment workflow"""
    print("🚀 RENTAL MANAGEMENT SYSTEM DEPLOYMENT")
    print("=" * 60)
    
    # Step 1: Backup current database
    backup_file = backup_before_deploy()
    
    # Step 2: Deploy to GitHub
    if deploy_to_github():
        print("\n✅ DEPLOYMENT SUCCESSFUL!")
        
        # Step 3: Post-deployment instructions
        post_deploy_setup()
        
        if backup_file:
            print(f"\n💾 BACKUP FILE: {backup_file}")
            print("Keep this backup file safe - you can restore it if needed!")
    else:
        print("\n❌ DEPLOYMENT FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
