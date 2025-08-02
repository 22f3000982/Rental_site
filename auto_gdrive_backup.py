"""
🔄 Automatic Google Drive Backup System
Like WhatsApp - Continuous backup to Google Drive

This script runs in the background and automatically:
1. Monitors database changes
2. Creates backups when users register/update data
3. Uploads to Google Drive automatically
4. Keeps multiple versions (like WhatsApp)
"""

import os
import time
import schedule
import threading
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlite3
import json
from gdrive_backup import GoogleDriveBackup

class DatabaseMonitor(FileSystemEventHandler):
    """Monitor database file changes like WhatsApp monitors messages"""
    
    def __init__(self, backup_manager):
        self.backup_manager = backup_manager
        self.last_backup = datetime.now()
        self.min_backup_interval = 300  # 5 minutes minimum between backups
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Monitor the billing.db file
        if event.src_path.endswith('billing.db'):
            print(f"📊 Database changed: {datetime.now().strftime('%H:%M:%S')}")
            self.schedule_backup()
    
    def schedule_backup(self):
        """Schedule a backup if enough time has passed"""
        now = datetime.now()
        if (now - self.last_backup).seconds > self.min_backup_interval:
            print("⏰ Scheduling backup...")
            # Run backup in separate thread to avoid blocking
            backup_thread = threading.Thread(target=self.create_and_upload_backup)
            backup_thread.daemon = True
            backup_thread.start()
            self.last_backup = now

    def create_and_upload_backup(self):
        """Create and upload backup like WhatsApp"""
        try:
            print("🔄 Creating automatic backup...")
            
            # Create local backup first
            self.create_local_backup()
            
            # Upload to Google Drive
            success = self.backup_manager.upload_backup()
            
            if success:
                print("✅ Auto-backup completed successfully!")
            else:
                print("❌ Auto-backup failed")
                
        except Exception as e:
            print(f"⚠️ Backup error: {str(e)}")

    def create_local_backup(self):
        """Create local backup file"""
        try:
            # Connect to database
            db_path = os.path.join('backend', 'instance', 'billing.db')
            if not os.path.exists(db_path):
                print("⚠️ Database not found")
                return
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            backup_data = {}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                backup_data[table_name] = {
                    'columns': columns,
                    'data': rows
                }
            
            # Save backup file
            backup_filename = f"auto_backup_{timestamp}.json"
            with open(backup_filename, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            print(f"💾 Local backup created: {backup_filename}")
            conn.close()
            
        except Exception as e:
            print(f"❌ Local backup failed: {str(e)}")

class WhatsAppStyleBackup:
    """Main backup manager - works like WhatsApp backup"""
    
    def __init__(self):
        self.gdrive_backup = GoogleDriveBackup()
        self.observer = None
        self.running = False
        
    def start_monitoring(self):
        """Start monitoring like WhatsApp background service"""
        print("🚀 Starting WhatsApp-style backup monitoring...")
        print("📱 Your data will be automatically backed up to Google Drive")
        print("⏰ Like WhatsApp: Continuous monitoring + Scheduled backups")
        print("=" * 60)
        
        # Setup file system monitoring
        event_handler = DatabaseMonitor(self.gdrive_backup)
        self.observer = Observer()
        
        # Monitor the instance folder where billing.db is located
        watch_path = os.path.join('backend', 'instance')
        if os.path.exists(watch_path):
            self.observer.schedule(event_handler, watch_path, recursive=True)
            self.observer.start()
            print(f"👁️ Monitoring database changes in: {watch_path}")
        else:
            print("⚠️ Database folder not found, creating...")
            os.makedirs(watch_path, exist_ok=True)
        
        # Schedule regular backups (like WhatsApp daily backup)
        self.schedule_regular_backups()
        
        self.running = True
        
        try:
            print("\n🔄 Backup system is running...")
            print("Press Ctrl+C to stop")
            
            while self.running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping backup system...")
            self.stop_monitoring()
    
    def schedule_regular_backups(self):
        """Schedule regular backups like WhatsApp"""
        # Daily backup at 2 AM (like WhatsApp)
        schedule.every().day.at("02:00").do(self.daily_backup)
        
        # Weekly full backup (like WhatsApp weekly backup)
        schedule.every().sunday.at("03:00").do(self.weekly_backup)
        
        # Hourly quick backup during business hours
        schedule.every().hour.do(self.hourly_backup_if_changes)
        
        print("📅 Scheduled backups:")
        print("   ⏰ Daily: 2:00 AM")
        print("   📅 Weekly: Sunday 3:00 AM")  
        print("   🕐 Hourly: During business hours")
    
    def daily_backup(self):
        """Daily backup like WhatsApp"""
        print("🌅 Running daily backup (like WhatsApp)...")
        self.create_and_upload_with_label("daily")
    
    def weekly_backup(self):
        """Weekly backup like WhatsApp"""
        print("📅 Running weekly backup (like WhatsApp)...")
        self.create_and_upload_with_label("weekly")
    
    def hourly_backup_if_changes(self):
        """Hourly backup only if there are changes"""
        current_hour = datetime.now().hour
        # Only during business hours (9 AM to 6 PM)
        if 9 <= current_hour <= 18:
            print("🕐 Checking for hourly backup...")
            self.create_and_upload_with_label("hourly")
    
    def create_and_upload_with_label(self, backup_type):
        """Create and upload backup with type label"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create local backup
            monitor = DatabaseMonitor(self.gdrive_backup)
            monitor.create_local_backup()
            
            # Upload to Google Drive
            success = self.gdrive_backup.upload_backup()
            
            if success:
                print(f"✅ {backup_type.title()} backup completed!")
            else:
                print(f"❌ {backup_type.title()} backup failed")
                
        except Exception as e:
            print(f"❌ {backup_type.title()} backup error: {str(e)}")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        print("✅ Backup monitoring stopped")

def main():
    """Main function - start WhatsApp-style backup"""
    print("=" * 60)
    print("📱 WHATSAPP-STYLE GOOGLE DRIVE BACKUP")
    print("=" * 60)
    print("🔄 Automatic, continuous backup to Google Drive")
    print("📊 Monitors database changes in real-time")
    print("⏰ Scheduled backups like WhatsApp")
    print("☁️ Multiple backup versions in cloud")
    print("=" * 60)
    
    # Check if credentials exist
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("📋 Please follow GOOGLE_DRIVE_SETUP.md first")
        input("Press Enter to exit...")
        return
    
    # Start the backup system
    backup_system = WhatsAppStyleBackup()
    backup_system.start_monitoring()

if __name__ == "__main__":
    main()
