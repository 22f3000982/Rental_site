# 🌐 How to Preserve Live Website User Data

## Problem
Users who register through the live website get lost during deployments because they're not in your local backup.

## Quick Solution (Manual)

### Step 1: Download Live User Data
1. **Go to your live site**: https://rental-site-8m2m.onrender.com/
2. **Login as admin** with your credentials 
3. **Navigate to Settings**: Click on "Settings" in admin dashboard
4. **Create Fresh Backup**: Click "Create Backup" button
5. **Download Backup**: Click "Download Backup" button
6. **Save the file** as `current_users_backup.json` in your `backend` folder

### Step 2: Deploy Safely
```bash
# Now your backup includes ALL users (local + live)
git add .
git commit -m "Include live website users in backup"
git push origin master
```

## Automated Solution

Run this script before each deployment:
```bash
python sync_live_data.py
```
- Enter your admin credentials
- Script downloads live data automatically
- Merges with local data
- Ready for safe deployment

## Better Workflow

### Before Every Deployment:
1. **Sync live data**: `python sync_live_data.py`
2. **Or manually**: Download backup from live admin panel
3. **Then deploy**: `git add . && git commit -m "..." && git push`

### After Deployment:
- Check that all users are restored
- Verify in admin panel that user count is correct

## Prevention

### Set up Regular Backups:
1. Create backups before major changes
2. Download backups periodically 
3. Store backups in multiple locations
4. Test restore process regularly

## Current Issue Recovery

To recover the lost user:
1. **Check if you have their registration info** (email, etc.)
2. **Ask them to re-register** (temporary solution)
3. **Or manually create their account** in admin panel
4. **Going forward**: Always sync live data before deployments

## Files Created:
- `sync_live_data.py` - Automated sync script
- Use existing admin panel backup features
- Manual download from live site works too

Remember: **Always backup live data before deployment!** 🔒
