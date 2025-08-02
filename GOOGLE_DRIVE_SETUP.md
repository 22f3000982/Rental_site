# 🚀 Google Drive Backup - Quick Setup Guide

## ⚡ 5-Minute Setup

### Step 1: Get Google Drive API Credentials
1. **Go to**: https://console.cloud.google.com/
2. **Create or select** a project
3. **Enable Google Drive API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google Drive API" → Enable
4. **Create credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop Application"
   - Name it "Rental Site Backup"
5. **Download JSON file** as `credentials.json`
6. **Put `credentials.json`** in your project root folder

### Step 2: First Time Setup
```bash
# The packages are already installed
# Just run the backup system
python gdrive_backup.py
```

### Step 3: Authenticate
- Browser will open automatically
- Login with your Google account
- Grant permissions
- Done! Token saved for future use

## 🔄 Daily Usage

### Before Deployment (Download latest from cloud):
```bash
python gdrive_backup.py
# Choose option 2: Download latest backup
```

### After Users Register (Upload to cloud):
```bash
python gdrive_backup.py
# Choose option 1: Upload current backup
```

### Or use the batch file:
```bash
gdrive_backup.bat
```

## 🎯 What This Solves

**Problem**: Users register on live site → you push code → users lost

**Solution**: 
1. **Download latest backup** from Google Drive (includes live users)
2. **Deploy** → all users restored automatically
3. **Upload new backup** to cloud for safety

## 🛡️ Your Workflow Now:

### Every Deployment:
```bash
# 1. Download latest backup (includes all live users)
python gdrive_backup.py  # Choose option 2

# 2. Deploy safely
git add .
git commit -m "Deploy with Google Drive backup"
git push origin master

# 3. Upload new backup after deployment (optional)
python gdrive_backup.py  # Choose option 1
```

## 🔧 Advanced Features

### Command Line Usage:
```bash
python gdrive_backup.py upload    # Upload backup
python gdrive_backup.py download  # Download backup
python gdrive_backup.py list      # List all backups
```

### Full Sync:
```bash
python gdrive_backup.py
# Choose option 4: Full sync
```

## 📁 Google Drive Structure
```
Google Drive/
└── Rental_Site_Backups/
    ├── latest_backup.json           ← Always current
    ├── rental_backup_20250801_143022.json
    ├── rental_backup_20250801_152015.json
    └── ...
```

## 🚨 Troubleshooting

### "credentials.json not found"
- Download from Google Cloud Console
- Put in project root folder

### "Authentication failed"
- Delete `token.pickle`
- Run script again
- Re-authenticate

### "No backup found"
- Run option 1 first (upload)
- Then try option 2 (download)

## ✅ You're All Set!

Your data is now **100% safe in the cloud**. No more lost users! 🎉

**Test it now**:
1. Run `python gdrive_backup.py`
2. Choose option 1 to upload
3. Check your Google Drive for the backup folder
4. Success! 🚀
