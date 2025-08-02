"""
🚀 Simple Database Backup - Just Works!
No complex file detection, no JSON parsing issues.
Direct database export/import using SQL.
"""

import os
import sqlite3
import shutil
from datetime import datetime
from flask import current_app

class SimpleDatabaseBackup:
    """Ultra-simple database backup system"""
    
    def __init__(self):
        self.backup_folder = "simple_backups"
        self.ensure_backup_folder()
    
    def ensure_backup_folder(self):
        """Create backup folder if it doesn't exist"""
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
    
    def get_database_path(self):
        """Get the correct database path"""
        possible_paths = [
            os.path.join('instance', 'billing.db'),  # When running from backend
            os.path.join('backend', 'instance', 'billing.db'),  # When running from root
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def create_backup(self):
        """Create a simple database backup by copying the SQLite file"""
        try:
            print("📁 Creating simple database backup...")
            
            # Get database path
            db_path = self.get_database_path()
            if not db_path:
                return {"success": False, "message": "Database not found"}
            
            print(f"📂 Database found at: {db_path}")
            
            # Create timestamped backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"simple_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_folder, backup_filename)
            
            # Simply copy the database file
            shutil.copy2(db_path, backup_path)
            
            # Also create a "latest" backup
            latest_path = os.path.join(self.backup_folder, "latest_backup.db")
            shutil.copy2(db_path, latest_path)
            
            # Get file size for info
            file_size = os.path.getsize(backup_path)
            
            print(f"✅ Backup created: {backup_filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "message": f"Backup created successfully! File: {backup_filename}",
                "filename": backup_filename,
                "filepath": backup_path,
                "size": file_size
            }
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return {"success": False, "message": f"Backup failed: {str(e)}"}
    
    def restore_backup(self, backup_filename=None):
        """Restore database from backup by replacing the database file"""
        try:
            print("🔄 Restoring from simple database backup...")
            
            # Find backup file to restore from
            if not backup_filename:
                # Use latest backup
                backup_path = os.path.join(self.backup_folder, "latest_backup.db")
                if not os.path.exists(backup_path):
                    # Look for any backup file
                    backup_files = [f for f in os.listdir(self.backup_folder) if f.endswith('.db')]
                    if not backup_files:
                        return {"success": False, "message": "No backup files found"}
                    
                    # Use most recent backup
                    backup_files.sort(reverse=True)
                    backup_path = os.path.join(self.backup_folder, backup_files[0])
            else:
                backup_path = os.path.join(self.backup_folder, backup_filename)
            
            if not os.path.exists(backup_path):
                return {"success": False, "message": f"Backup file not found: {backup_path}"}
            
            print(f"📂 Using backup file: {backup_path}")
            
            # Get current database path
            db_path = self.get_database_path()
            if not db_path:
                return {"success": False, "message": "Database not found"}
            
            # Create backup of current database first
            current_backup = f"current_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if os.path.exists(db_path):
                shutil.copy2(db_path, current_backup)
                print(f"💾 Current database backed up as: {current_backup}")
            
            # Simply replace the database file
            shutil.copy2(backup_path, db_path)
            
            # Verify the restore worked by checking the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count users to verify
            cursor.execute("SELECT COUNT(*) FROM user")
            user_count = cursor.fetchone()[0]
            
            # Count tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✅ Database restored! {table_count} tables, {user_count} users")
            
            return {
                "success": True,
                "message": f"Database restored successfully! {table_count} tables, {user_count} users found",
                "tables": table_count,
                "users": user_count,
                "backup_file": os.path.basename(backup_path)
            }
            
        except Exception as e:
            print(f"❌ Restore failed: {str(e)}")
            return {"success": False, "message": f"Restore failed: {str(e)}"}
    
    def list_backups(self):
        """List all available backup files"""
        backups = []
        
        if os.path.exists(self.backup_folder):
            for file in os.listdir(self.backup_folder):
                if file.endswith('.db'):
                    filepath = os.path.join(self.backup_folder, file)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': file,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'is_latest': file == 'latest_backup.db'
                    })
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups
    
    def get_backup_info(self):
        """Get backup information for display"""
        backups = self.list_backups()
        
        if backups:
            latest = backups[0]
            return {
                "exists": True,
                "filename": latest['filename'],
                "size": latest['size'],
                "date": latest['modified'],
                "total_backups": len(backups)
            }
        
        return {"exists": False}

# Global instance
simple_db_backup = SimpleDatabaseBackup()
