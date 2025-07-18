#!/usr/bin/env python3
"""
Email Configuration Setup Script
Run this script to easily configure Gmail email settings
"""

import os
import sys

def setup_email_config():
    print("🔧 Email Configuration Setup")
    print("=" * 50)
    
    # Check current .env file
    env_file = '.env'
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        return
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    print("📧 Current Email Settings:")
    print("   Email: ashraj77777@gmail.com")
    print("   Server: smtp.gmail.com:587")
    
    # Check if already configured
    mail_enabled = False
    mail_password = ""
    
    for line in lines:
        if line.startswith('MAIL_ENABLED='):
            mail_enabled = line.split('=')[1].strip().lower() == 'true'
        elif line.startswith('MAIL_PASSWORD='):
            mail_password = line.split('=')[1].strip()
    
    if mail_enabled and mail_password:
        print("✅ Email appears to be configured!")
        choice = input("Do you want to reconfigure? (y/N): ")
        if choice.lower() != 'y':
            return
    
    print("\n🔐 Gmail App Password Setup Required:")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification (if not already enabled)")
    print("3. Go to: https://myaccount.google.com/apppasswords")
    print("4. Select 'Mail' and 'Windows Computer'")
    print("5. Generate the 16-character password")
    print()
    
    # Get app password from user
    app_password = input("Enter your Gmail App Password (16 characters): ").strip()
    
    if len(app_password) != 16:
        print("❌ Gmail App Passwords are exactly 16 characters!")
        print("   Example: abcd efgh ijkl mnop")
        return
    
    # Update .env file
    new_lines = []
    updated_password = False
    updated_enabled = False
    
    for line in lines:
        if line.startswith('MAIL_PASSWORD='):
            new_lines.append(f'MAIL_PASSWORD={app_password}\n')
            updated_password = True
        elif line.startswith('MAIL_ENABLED='):
            new_lines.append('MAIL_ENABLED=True\n')
            updated_enabled = True
        else:
            new_lines.append(line)
    
    # Add missing lines if needed
    if not updated_password:
        new_lines.append(f'MAIL_PASSWORD={app_password}\n')
    if not updated_enabled:
        new_lines.append('MAIL_ENABLED=True\n')
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Email configuration updated!")
    print("🔄 Please restart your Flask application for changes to take effect.")
    print()
    print("📧 Test email setup by:")
    print("   1. Restart the Flask app")
    print("   2. Go to Admin > Send Email")
    print("   3. Send a test email to yourself")

if __name__ == "__main__":
    setup_email_config()
