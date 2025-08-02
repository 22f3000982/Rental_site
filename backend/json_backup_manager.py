"""
📁 JSON Backup System - Super Simple File Download/Upload
Just like manual file backup - download JSON, upload before deploy
"""

import os
import json
import sqlite3
from datetime import datetime
import shutil
from flask import current_app

class JSONBackupManager:
    """Simple JSON file backup system"""
    
    def __init__(self):
        self.backup_folder = "json_backups"
        self.ensure_backup_folder()
    
    def ensure_backup_folder(self):
        """Create backup folder if it doesn't exist"""
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
    
    def create_json_backup(self):
        """Create a JSON backup file for download"""
        try:
            print("📁 Creating JSON backup file...")
            
            # Connect to database
            db_path = os.path.join('backend', 'instance', 'billing.db')
            if not os.path.exists(db_path):
                db_path = os.path.join('instance', 'billing.db')  # Try relative path
            
            if not os.path.exists(db_path):
                return {"success": False, "message": "Database not found"}
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            backup_data = {
                'backup_info': {
                    'created_at': datetime.now().isoformat(),
                    'backup_type': 'json_manual',
                    'description': 'Manual JSON backup for file download/upload'
                },
                'tables': {}
            }
            
            # Backup each table
            total_records = 0
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                backup_data['tables'][table_name] = {
                    'columns': columns,
                    'data': rows
                }
                total_records += len(rows)
                print(f"✅ Backed up table: {table_name} ({len(rows)} records)")
            
            # Save backup file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"rental_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_folder, backup_filename)
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Also save as latest backup
            latest_path = os.path.join(self.backup_folder, "latest_backup.json")
            with open(latest_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            conn.close()
            print(f"💾 JSON backup created: {backup_filename}")
            
            return {
                "success": True, 
                "message": f"JSON backup created successfully! ({len(tables)} tables, {total_records} records)",
                "filename": backup_filename,
                "filepath": backup_path,
                "tables_count": len(tables),
                "records_count": total_records
            }
            
        except Exception as e:
            print(f"❌ JSON backup failed: {str(e)}")
            return {"success": False, "message": f"Backup failed: {str(e)}"}
    
    def restore_from_json(self, json_file_path=None):
        """Restore from JSON backup file"""
        try:
            print("🔄 Restoring from JSON backup...")
            
            # Find JSON file to restore from
            if not json_file_path:
                # Look for uploaded JSON files in backend folder
                backend_json_files = []
                
                # Check backend folder
                if os.path.exists('backend'):
                    for file in os.listdir('backend'):
                        if file.endswith('.json') and 'backup' in file.lower():
                            backend_json_files.append(os.path.join('backend', file))
                
                # Check current folder
                for file in os.listdir('.'):
                    if file.endswith('.json') and 'backup' in file.lower():
                        backend_json_files.append(file)
                
                # Check backup folder
                backup_folder_files = []
                if os.path.exists(self.backup_folder):
                    for file in os.listdir(self.backup_folder):
                        if file.endswith('.json'):
                            backup_folder_files.append(os.path.join(self.backup_folder, file))
                
                # Use most recent file
                all_files = backend_json_files + backup_folder_files
                if not all_files:
                    return {"success": False, "message": "No JSON backup files found"}
                
                # Sort by modification time (most recent first)
                all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                json_file_path = all_files[0]
                print(f"📂 Using backup file: {json_file_path}")
            
            if not os.path.exists(json_file_path):
                return {"success": False, "message": f"Backup file not found: {json_file_path}"}
            
            # Load backup data with error handling
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            except json.JSONDecodeError as e:
                return {"success": False, "message": f"Invalid JSON file: {str(e)}"}
            except Exception as e:
                return {"success": False, "message": f"Error reading backup file: {str(e)}"}
            
            print(f"📄 Backup file loaded. Keys: {list(backup_data.keys())}")
            
            # Check if backup data has the expected structure
            if 'tables' not in backup_data:
                return {"success": False, "message": "Invalid backup file format: 'tables' key not found"}
            
            if not isinstance(backup_data['tables'], dict):
                return {"success": False, "message": "Invalid backup file format: 'tables' is not a dictionary"}
            
            print(f"📊 Found tables in backup: {list(backup_data['tables'].keys())}")
            
            # Connect to database
            possible_db_paths = [
                os.path.join('instance', 'billing.db'),  # When running from backend directory
                os.path.join('backend', 'instance', 'billing.db'),  # When running from root directory
            ]
            
            db_path = None
            for path in possible_db_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if not db_path:
                return {"success": False, "message": f"Database not found. Checked paths: {possible_db_paths}"}
            
            print(f"📁 Using database: {db_path}")
            
            # Create backup of current database first
            if os.path.exists(db_path):
                backup_current = f"current_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, backup_current)
                print(f"💾 Current database backed up as: {backup_current}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
            except Exception as e:
                return {"success": False, "message": f"Database connection failed: {str(e)}"}
            
            restored_tables = 0
            restored_records = 0
            
            # Restore each table
            try:
                for table_name, table_data in backup_data['tables'].items():
                    try:
                        print(f"🔄 Processing table: {table_name}")
                        
                        # Validate table data structure
                        if not isinstance(table_data, dict):
                            print(f"⚠️ Skipping {table_name}: invalid data structure")
                            continue
                            
                        if 'columns' not in table_data or 'data' not in table_data:
                            print(f"⚠️ Skipping {table_name}: missing columns or data")
                            continue
                        
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
                        # Continue with other tables
                        
            except Exception as e:
                conn.close()
                return {"success": False, "message": f"Error accessing backup tables: {str(e)}"}
            
            conn.commit()
            conn.close()
            
            # Move the restored file to processed folder
            processed_folder = "processed_backups"
            if not os.path.exists(processed_folder):
                os.makedirs(processed_folder)
            
            processed_filename = f"processed_{os.path.basename(json_file_path)}"
            shutil.move(json_file_path, os.path.join(processed_folder, processed_filename))
            print(f"📁 Moved processed backup to: {processed_filename}")
            
            print(f"🎉 JSON restore completed! {restored_tables} tables, {restored_records} records")
            
            return {
                "success": True,
                "message": f"JSON restore completed! {restored_tables} tables and {restored_records} records restored",
                "tables_restored": restored_tables,
                "records_restored": restored_records,
                "backup_info": backup_data.get('backup_info', {})
            }
            
        except Exception as e:
            print(f"❌ JSON restore failed: {str(e)}")
            return {"success": False, "message": f"Restore failed: {str(e)}"}
    
    def list_available_backups(self):
        """List all available JSON backup files"""
        backups = []
        
        # Check backup folder
        if os.path.exists(self.backup_folder):
            for file in os.listdir(self.backup_folder):
                if file.endswith('.json'):
                    filepath = os.path.join(self.backup_folder, file)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': file,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Check backend folder for uploaded files
        if os.path.exists('backend'):
            for file in os.listdir('backend'):
                if file.endswith('.json') and 'backup' in file.lower():
                    filepath = os.path.join('backend', file)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': file,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'location': 'backend (uploaded)'
                    })
        
        # Sort by modification time (most recent first)
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups
    
    def get_backup_info(self):
        """Get information about latest backup"""
        latest_path = os.path.join(self.backup_folder, "latest_backup.json")
        
        if os.path.exists(latest_path):
            try:
                with open(latest_path, 'r') as f:
                    backup_data = json.load(f)
                
                return {
                    "exists": True,
                    "date": backup_data.get('backup_info', {}).get('created_at', 'Unknown'),
                    "tables": len(backup_data.get('tables', {})),
                    "records": sum(len(table.get('data', [])) for table in backup_data.get('tables', {}).values()),
                    "filepath": latest_path
                }
            except:
                pass
        
        return {"exists": False}

# Global instance
json_backup_manager = JSONBackupManager()
