#!/usr/bin/env python3
"""
Google Drive Backup Integration - Enhanced Version
Automatically backs up to Google Drive and restores from there
"""

import os
import json
import pickle
import sys
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveBackup:
    def __init__(self):
        self.service = None
        self.backup_folder_id = None
        
    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # Load existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"⚠️  Token refresh failed: {e}")
                    # Delete old token and re-authenticate
                    if os.path.exists('token.pickle'):
                        os.remove('token.pickle')
                    creds = None
            
            if not creds:
                if not os.path.exists('credentials.json'):
                    print("❌ credentials.json not found!")
                    print("\n📋 To get credentials.json:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create project or select existing")
                    print("3. Enable Google Drive API")
                    print("4. Go to Credentials → Create → OAuth 2.0 Client IDs")
                    print("5. Choose 'Desktop Application'")
                    print("6. Download JSON file as 'credentials.json'")
                    print("7. Put it in this folder")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"❌ Authentication failed: {e}")
                    return False
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ Successfully authenticated with Google Drive")
            return True
        except Exception as e:
            print(f"❌ Failed to build Drive service: {e}")
            return False
    
    def create_backup_folder(self):
        """Create or find the backup folder in Google Drive"""
        try:
            folder_name = "Rental_Site_Backups"
            
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                self.backup_folder_id = items[0]['id']
                print(f"✅ Found existing backup folder: {folder_name}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                self.backup_folder_id = folder.get('id')
                print(f"✅ Created new backup folder: {folder_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup folder: {e}")
            return False
    
    def create_local_backup(self):
        """Create local backup before uploading"""
        try:
            print("📊 Creating local backup...")
            
            # Try different backup creation methods
            if os.path.exists('backend/create_backup.py'):
                os.system('cd backend && python create_backup.py')
            elif os.path.exists('create_backup.py'):
                os.system('python create_backup.py')
            else:
                print("⚠️  No backup creation script found, checking for existing backup...")
            
            # Check for backup files
            backup_files = [
                'backend/current_backup.json',
                'backend/current_users_backup.json',
                'current_backup.json',
                'current_users_backup.json'
            ]
            
            for backup_file in backup_files:
                if os.path.exists(backup_file):
                    print(f"✅ Found backup file: {backup_file}")
                    return backup_file
            
            print("❌ No backup file found!")
            return None
            
        except Exception as e:
            print(f"❌ Error creating local backup: {e}")
            return None
    
    def upload_backup(self, backup_file_path):
        """Upload backup file to Google Drive"""
        try:
            if not os.path.exists(backup_file_path):
                print(f"❌ Backup file not found: {backup_file_path}")
                return False
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            drive_filename = f"rental_backup_{timestamp}.json"
            
            file_metadata = {
                'name': drive_filename,
                'parents': [self.backup_folder_id]
            }
            
            media = MediaFileUpload(backup_file_path, mimetype='application/json')
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size'
            ).execute()
            
            # Get file size for display
            file_size = int(file.get('size', 0))
            size_kb = file_size / 1024
            
            print(f"✅ Backup uploaded to Google Drive: {drive_filename}")
            print(f"📁 File ID: {file.get('id')}")
            print(f"💾 Size: {size_kb:.1f} KB")
            
            # Also upload as "latest_backup.json" for easy access
            latest_metadata = {
                'name': 'latest_backup.json',
                'parents': [self.backup_folder_id]
            }
            
            # Delete existing latest_backup.json if it exists
            self.delete_file_by_name('latest_backup.json')
            
            # Create new media upload instance
            media_latest = MediaFileUpload(backup_file_path, mimetype='application/json')
            
            latest_file = self.service.files().create(
                body=latest_metadata,
                media_body=media_latest,
                fields='id,name'
            ).execute()
            
            print(f"✅ Latest backup also saved as: latest_backup.json")
            
            return True
            
        except Exception as e:
            print(f"❌ Error uploading backup: {e}")
            return False
    
    def download_latest_backup(self, local_filename=None):
        """Download latest backup from Google Drive"""
        try:
            # Determine local filename
            if not local_filename:
                if os.path.exists('backend'):
                    local_filename = 'backend/current_users_backup.json'
                else:
                    local_filename = 'current_users_backup.json'
            
            # Search for latest_backup.json
            results = self.service.files().list(
                q=f"name='latest_backup.json' and parents in '{self.backup_folder_id}' and trashed=false",
                spaces='drive',
                fields='files(id,name,modifiedTime,size)'
            ).execute()
            
            items = results.get('files', [])
            
            if not items:
                print("❌ No latest backup found in Google Drive")
                print("💡 Try uploading a backup first")
                return False
            
            file_info = items[0]
            file_id = file_info['id']
            modified_time = file_info.get('modifiedTime', 'Unknown')
            file_size = int(file_info.get('size', 0))
            size_kb = file_size / 1024
            
            print(f"📥 Downloading backup from Google Drive...")
            print(f"📅 Last modified: {modified_time[:10]}")
            print(f"💾 Size: {size_kb:.1f} KB")
            
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"\r⬇️  Progress: {progress}%", end='', flush=True)
            
            print()  # New line after progress
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_filename) if os.path.dirname(local_filename) else '.', exist_ok=True)
            
            # Save to local file
            with open(local_filename, 'wb') as f:
                f.write(file_io.getvalue())
            
            # Verify the downloaded file
            try:
                with open(local_filename, 'r') as f:
                    data = json.load(f)
                    if 'user' in data or 'users' in data:
                        print(f"✅ Valid backup downloaded: {local_filename}")
                        
                        # Show user count
                        if 'user' in data and 'data' in data['user']:
                            user_count = len(data['user']['data'])
                            print(f"👥 Contains {user_count} users")
                        elif 'users' in data:
                            user_count = len(data['users'])
                            print(f"👥 Contains {user_count} users")
                        
                        return True
                    else:
                        print("⚠️  Downloaded file doesn't appear to be a valid backup")
                        return False
            except json.JSONDecodeError:
                print("❌ Downloaded file is not valid JSON")
                return False
            
        except Exception as e:
            print(f"❌ Error downloading backup: {e}")
            return False
    
    def delete_file_by_name(self, filename):
        """Delete file by name from backup folder"""
        try:
            results = self.service.files().list(
                q=f"name='{filename}' and parents in '{self.backup_folder_id}' and trashed=false",
                spaces='drive'
            ).execute()
            
            items = results.get('files', [])
            for item in items:
                self.service.files().delete(fileId=item['id']).execute()
                
        except Exception as e:
            pass  # Ignore errors when deleting
    
    def list_backups(self):
        """List all backup files in Google Drive"""
        try:
            results = self.service.files().list(
                q=f"parents in '{self.backup_folder_id}' and trashed=false",
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime, size)',
                orderBy='modifiedTime desc'
            ).execute()
            
            items = results.get('files', [])
            
            if not items:
                print("📂 No backup files found in Google Drive")
                return []
            
            print(f"📂 Found {len(items)} backup files:")
            print("-" * 80)
            
            for i, item in enumerate(items, 1):
                name = item['name']
                created = item.get('createdTime', 'Unknown')[:10]
                modified = item.get('modifiedTime', 'Unknown')[:10]
                size = int(item.get('size', 0))
                size_kb = size / 1024
                
                print(f"{i:2d}. {name}")
                print(f"    📅 Created: {created} | Modified: {modified} | Size: {size_kb:.1f} KB")
                
                if name == 'latest_backup.json':
                    print("    ⭐ This is the latest backup")
                print()
            
            return items
            
        except Exception as e:
            print(f"❌ Error listing backups: {e}")
            return []

def main():
    print("☁️  Google Drive Backup System for Rental Site")
    print("=" * 60)
    
    backup_system = GoogleDriveBackup()
    
    # Authenticate with Google Drive
    print("\n🔐 Authenticating with Google Drive...")
    if not backup_system.authenticate():
        print("\n❌ Authentication failed. Please check the setup guide.")
        input("Press Enter to exit...")
        return
    
    # Create/find backup folder
    print("\n📁 Setting up backup folder...")
    if not backup_system.create_backup_folder():
        print("\n❌ Failed to create backup folder.")
        input("Press Enter to exit...")
        return
    
    # Check if running as script with arguments
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == 'upload':
            backup_file = backup_system.create_local_backup()
            if backup_file:
                backup_system.upload_backup(backup_file)
            return
        elif action == 'download':
            backup_system.download_latest_backup()
            return
        elif action == 'list':
            backup_system.list_backups()
            return
    
    # Interactive menu
    while True:
        print("\n" + "="*60)
        print("Choose an option:")
        print("1. 📤 Upload current backup to Google Drive")
        print("2. 📥 Download latest backup from Google Drive")
        print("3. 📂 List all backups in Google Drive")
        print("4. 🔄 Full sync (upload current, then download latest)")
        print("5. 🚪 Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            print("\n📊 Creating and uploading backup...")
            backup_file = backup_system.create_local_backup()
            if backup_file:
                success = backup_system.upload_backup(backup_file)
                if success:
                    print("\n🎉 Backup successfully uploaded to Google Drive!")
                    print("💡 You can now deploy safely - your data is backed up in the cloud")
            else:
                print("\n❌ Failed to create local backup")
        
        elif choice == '2':
            print("\n📥 Downloading latest backup from Google Drive...")
            success = backup_system.download_latest_backup()
            if success:
                print("\n🎉 Latest backup downloaded successfully!")
                print("✅ Ready for deployment! All current users (including from live site) are now in your local backup")
                print("\n💡 You can now safely:")
                print("   git add .")
                print("   git commit -m 'Deploy with latest Google Drive backup'")
                print("   git push origin master")
            else:
                print("\n❌ Failed to download backup")
        
        elif choice == '3':
            print("\n📂 Listing all backups in Google Drive...")
            backup_system.list_backups()
        
        elif choice == '4':
            print("\n🔄 Performing full sync...")
            
            # Upload current backup
            print("📤 Step 1: Uploading current backup...")
            backup_file = backup_system.create_local_backup()
            if backup_file:
                upload_success = backup_system.upload_backup(backup_file)
            else:
                upload_success = False
            
            # Download latest backup
            print("\n📥 Step 2: Downloading latest backup...")
            download_success = backup_system.download_latest_backup()
            
            if upload_success and download_success:
                print("\n🎉 Full sync completed successfully!")
                print("✅ Your local and cloud backups are now synchronized")
            else:
                print("\n⚠️  Sync completed with some issues")
        
        elif choice == '5':
            print("\n� Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
