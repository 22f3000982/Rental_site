# ☁️ Google Drive Backup Integration

## 🎯 What This Does:
- **Automatically uploads** your backup files to Google Drive
- **Downloads latest backup** from Google Drive before deployment
- **Cloud storage** ensures backups are never lost
- **Version history** keeps multiple backup versions
- **Cross-device access** - backup from anywhere

## 🚀 Setup Instructions

### Step 1: Install Required Packages
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Step 2: Enable Google Drive API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Choose **Desktop Application**
6. Download the JSON file as `credentials.json`
7. Put `credentials.json` in your project root folder

### Step 3: First Time Authentication
```bash
python gdrive_backup.py
```
- Choose option 1 to upload first backup
- Browser will open for Google authentication
- Grant permissions to access Google Drive
- Token will be saved for future use

## 🔄 Usage Workflow

### Before Every Deployment:
```bash
# Method 1: Upload current backup to Google Drive
python gdrive_backup.py
# Choose option 1

# Method 2: Download latest backup from Google Drive  
python gdrive_backup.py
# Choose option 2

# Then deploy safely
git add .
git commit -m "Deploy with Google Drive backup"
git push origin master
```

### After Users Register on Live Site:
```bash
# Download latest backup (includes new users)
python gdrive_backup.py
# Choose option 2

# This downloads all current live users to local backup
# Now you can deploy safely without losing anyone
```

## 🛠️ Advanced Features

### List All Backups:
```bash
python gdrive_backup.py
# Choose option 3
```

### Automatic Backup in App:
Add this to your Flask app to auto-backup to Google Drive when users register.

### Multiple Backup Versions:
- Each backup gets timestamped filename
- `latest_backup.json` always contains newest data  
- Old backups preserved for history

## 📁 File Structure After Setup:
```
Rental_site/
├── gdrive_backup.py          # Google Drive integration
├── credentials.json          # Google API credentials (don't commit)
├── token.pickle             # Authentication token (don't commit)
├── backend/
│   ├── current_users_backup.json  # Local backup file
│   └── ...
```

## 🔒 Security Notes:
- Add to `.gitignore`:
  ```
  credentials.json
  token.pickle
  ```
- Keep `credentials.json` secure
- Token auto-refreshes when needed

## 🌟 Benefits:
- ✅ **Never lose user data** - cloud backup always available
- ✅ **Sync across devices** - download backup from any computer  
- ✅ **Version history** - multiple backup versions preserved
- ✅ **Easy workflow** - one command to sync data
- ✅ **Automatic** - can be integrated into deployment pipeline

## 🚨 Emergency Recovery:
If everything fails, you can always:
1. Go to Google Drive
2. Open "Rental_Site_Backups" folder
3. Download `latest_backup.json`
4. Rename to `current_users_backup.json`
5. Put in `backend` folder
6. Deploy normally

**This is the most robust backup solution! Your data will be safe in the cloud.** ☁️🔒
