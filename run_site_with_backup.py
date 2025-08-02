"""
🚀 Combined Flask App + Auto Backup System
Runs your rental site AND backup monitoring in one process!

No need for multiple terminals - everything in one!
"""

import threading
import time
from backend.app import app
from auto_gdrive_backup import WhatsAppStyleBackup
import os

class CombinedRentalSiteBackup:
    """Run Flask app and backup system together"""
    
    def __init__(self):
        self.backup_system = None
        self.flask_thread = None
        self.backup_thread = None
        
    def start_flask_app(self):
        """Start Flask app in a separate thread"""
        print("🌐 Starting rental site on http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    def start_backup_system(self):
        """Start backup monitoring in a separate thread"""
        try:
            print("📱 Starting WhatsApp-style backup monitoring...")
            self.backup_system = WhatsAppStyleBackup()
            self.backup_system.start_monitoring()
        except Exception as e:
            print(f"❌ Backup system error: {str(e)}")
    
    def run_everything(self):
        """Run both Flask app and backup system together"""
        print("=" * 70)
        print("🚀 RENTAL SITE + WHATSAPP-STYLE BACKUP")
        print("=" * 70)
        print("🌐 Your rental site: http://localhost:5000")
        print("📱 Auto backup: Monitoring database changes")
        print("⏰ Scheduled backups: Daily + Weekly + Instant")
        print("☁️ Cloud storage: Google Drive")
        print("=" * 70)
        print()
        
        # Check credentials
        if not os.path.exists('credentials.json'):
            print("❌ credentials.json not found!")
            print("📋 Please run 'python gdrive_backup.py' first for one-time setup")
            input("Press Enter to exit...")
            return
        
        try:
            # Start Flask app in background thread
            self.flask_thread = threading.Thread(target=self.start_flask_app)
            self.flask_thread.daemon = True
            self.flask_thread.start()
            print("✅ Rental site started successfully!")
            
            # Give Flask a moment to start
            time.sleep(2)
            
            # Start backup system in main thread
            self.start_backup_system()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down rental site and backup system...")
            print("✅ Everything stopped safely!")

def main():
    """Main function"""
    # Change to the correct directory
    if os.path.basename(os.getcwd()) != 'Rental_site':
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
    
    combined_system = CombinedRentalSiteBackup()
    combined_system.run_everything()

if __name__ == "__main__":
    main()
