"""
🎯 Simple Google Drive Backup - Just like WhatsApp!

No complex setup - just:
1. Give us your Google Drive folder URL
2. Click backup button in admin
3. Restore popup when needed

SUPER SIMPLE!
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import shutil

class SimpleGDriveBackup:
    """Simple Google Drive backup - like WhatsApp but easier!"""
    
    def __init__(self):
        self.backup_folder_url = self.load_gdrive_folder()
        self.backup_file = "simple_backup.json"
        
    def load_gdrive_folder(self):
        """Load Google Drive folder URL from config"""
        config_file = "gdrive_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('folder_url', '')
        return ''
    
    def save_gdrive_folder(self, folder_url):
        """Save Google Drive folder URL"""
        config = {'folder_url': folder_url, 'setup_date': datetime.now().isoformat()}
        with open('gdrive_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        self.backup_folder_url = folder_url
        return True
    
    def create_backup(self):
        """Create simple backup file - like WhatsApp"""
        try:
            print("📱 Creating WhatsApp-style backup...")
            
            # Connect to database - check multiple possible paths
            possible_paths = [
                os.path.join('instance', 'billing.db'),  # When running from backend directory
                os.path.join('backend', 'instance', 'billing.db'),  # When running from root directory
            ]
            
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if not db_path:
                return {"success": False, "message": f"Database not found. Checked paths: {possible_paths}"}
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            backup_data = {
                'backup_date': datetime.now().isoformat(),
                'backup_type': 'whatsapp_style',
                'tables': {}
            }
            
            # Backup each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                backup_data['tables'][table_name] = {
                    'columns': columns,
                    'data': rows
                }
                print(f"✅ Backed up table: {table_name} ({len(rows)} records)")
            
            # Save backup file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"whatsapp_backup_{timestamp}.json"
            
            with open(backup_filename, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Also save as latest backup
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            conn.close()
            print(f"💾 Backup created: {backup_filename}")
            
            return {
                "success": True, 
                "message": f"Backup created successfully! ({len(tables)} tables backed up)",
                "filename": backup_filename,
                "tables_count": len(tables)
            }
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return {"success": False, "message": f"Backup failed: {str(e)}"}
    
    def restore_backup(self, backup_file=None):
        """Restore from backup - like WhatsApp restore"""
        try:
            print("🔄 Restoring from WhatsApp-style backup...")
            
            # Use latest backup if no specific file provided
            if not backup_file:
                backup_file = self.backup_file
            
            if not os.path.exists(backup_file):
                return {"success": False, "message": "No backup file found"}
            
            # Load backup data
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Connect to database - check multiple possible paths
            possible_paths = [
                os.path.join('instance', 'billing.db'),  # When running from backend directory
                os.path.join('backend', 'instance', 'billing.db'),  # When running from root directory
            ]
            
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if not db_path:
                return {"success": False, "message": f"Database not found. Checked paths: {possible_paths}"}
            
            # Create backup of current database first
            backup_current = f"current_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_current)
            print(f"💾 Current database backed up as: {backup_current}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            restored_tables = 0
            restored_records = 0
            
            # Restore each table
            for table_name, table_data in backup_data['tables'].items():
                try:
                    # Clear existing data
                    cursor.execute(f"DELETE FROM {table_name}")
                    
                    if table_data['data']:
                        # Prepare insert statement
                        columns = table_data['columns']
                        placeholders = ','.join(['?' for _ in columns])
                        insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                        
                        # Insert data
                        cursor.executemany(insert_sql, table_data['data'])
                        restored_records += len(table_data['data'])
                    
                    restored_tables += 1
                    print(f"✅ Restored table: {table_name} ({len(table_data['data'])} records)")
                    
                except Exception as e:
                    print(f"⚠️ Error restoring table {table_name}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            print(f"🎉 Restore completed! {restored_tables} tables, {restored_records} records")
            
            return {
                "success": True,
                "message": f"Restore completed! {restored_tables} tables and {restored_records} records restored",
                "tables_restored": restored_tables,
                "records_restored": restored_records,
                "backup_date": backup_data.get('backup_date', 'Unknown')
            }
            
        except Exception as e:
            print(f"❌ Restore failed: {str(e)}")
            return {"success": False, "message": f"Restore failed: {str(e)}"}
    
    def upload_to_gdrive(self, file_path):
        """Simple upload to Google Drive folder (using public folder)"""
        # This is a placeholder - in real implementation, you would:
        # 1. Use Google Drive API with service account
        # 2. Or use a simple file sharing method
        # For now, we'll simulate success
        print(f"📤 Uploading {file_path} to Google Drive...")
        print("✅ Upload successful! (Simulated)")
        return True
    
    def download_from_gdrive(self):
        """Simple download from Google Drive folder"""
        # This is a placeholder - in real implementation, you would:
        # 1. Download latest backup from Google Drive
        # 2. Or use a simple file sharing method
        print("📥 Downloading latest backup from Google Drive...")
        print("✅ Download successful! (Simulated)")
        return True
    
    def check_for_restore_needed(self):
        """Check if restore is needed (like WhatsApp on app startup)"""
        # Check if there's a backup available and database is empty/old
        possible_paths = [
            os.path.join('instance', 'billing.db'),  # When running from backend directory
            os.path.join('backend', 'instance', 'billing.db'),  # When running from root directory
        ]
        
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            return True  # Database doesn't exist, restore needed
        
        if os.path.exists(self.backup_file):
            # Check if backup is newer than database
            backup_time = os.path.getmtime(self.backup_file)
            db_time = os.path.getmtime(db_path)
            
            if backup_time > db_time:
                return True  # Backup is newer, restore might be needed
        
        return False
    
    def get_backup_info(self):
        """Get backup information for display"""
        if os.path.exists(self.backup_file):
            with open(self.backup_file, 'r') as f:
                backup_data = json.load(f)
            
            return {
                "exists": True,
                "date": backup_data.get('backup_date', 'Unknown'),
                "tables": len(backup_data.get('tables', {})),
                "records": sum(len(table.get('data', [])) for table in backup_data.get('tables', {}).values())
            }
        
        return {"exists": False}

# Global instance
simple_backup = SimpleGDriveBackup()
