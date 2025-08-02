"""
Test script to verify the simple backup system works
"""
import os
import sys

# Change to the backend directory (simulate running Flask app from backend)
backend_dir = r"c:\MY_PROJECTS\Rental_site\backend"
os.chdir(backend_dir)

# Add the parent directory to sys.path to import simple_gdrive_backup
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

print(f"Current working directory: {os.getcwd()}")
print(f"Parent directory added to path: {parent_dir}")

try:
    from simple_gdrive_backup import simple_backup
    print("✅ Successfully imported simple_gdrive_backup")
    
    # Test database path detection
    possible_paths = [
        os.path.join('instance', 'billing.db'),
        os.path.join('backend', 'instance', 'billing.db'),
    ]
    
    print("\nTesting database path detection:")
    for path in possible_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✅ EXISTS' if exists else '❌ NOT FOUND'}")
    
    # Test backup info
    print("\nTesting backup info:")
    backup_info = simple_backup.get_backup_info()
    print(f"  Backup info: {backup_info}")
    
    # Test create backup
    print("\nTesting create backup:")
    result = simple_backup.create_backup()
    print(f"  Backup result: {result}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
