# 🚀 Data Persistence Deployment Guide

This guide ensures your user data persists across deployments and prevents data loss.

## 🛡️ Data Protection System

Your application now has an automatic data protection system that:
- ✅ Creates backups automatically in production
- ✅ Restores data when the database is empty
- ✅ Provides manual backup controls in admin panel
- ✅ Supports multiple backup formats

## 📋 Pre-Deployment Steps

### Method 1: Using Backup Script (Recommended)

#### For Windows:
```bash
# Double-click this file or run in command prompt
backup_before_deploy.bat
```

#### For Python:
```bash
python create_backup.py
```

### Method 2: Using Admin Panel
1. Login as admin
2. Go to Settings page
3. Scroll to "Data Backup & Restore" section
4. Click "Create Backup"
5. Click "Download Backup" to save locally

## 🚀 Deployment Process

### Step 1: Create Backup
```bash
# Run the backup script
python create_backup.py
```

### Step 2: Commit Changes
```bash
git add .
git commit -m "Update with data persistence features"
```

### Step 3: Push to Repository
```bash
git push origin main
```

### Step 4: Deploy
- **Render**: Automatic deployment from GitHub
- **Railway**: Automatic deployment from GitHub  
- **Heroku**: `git push heroku main`

## 🔄 How Automatic Restore Works

1. **On App Startup**: App checks if there are any renter users
2. **If Database Empty**: Looks for backup files:
   - `current_backup.json` (newest)
   - `current_users_backup.json` 
   - `pre_deploy_backup_*.json` (sorted by date)
3. **Automatic Restore**: Restores all users and data from backup
4. **Logging**: Shows restoration progress in app logs

## 📁 Backup Files Created

- `current_backup.json` - Latest full backup
- `current_users_backup.json` - User data backup
- `pre_deploy_backup_YYYYMMDD_HHMMSS.json` - Timestamped backups
- `backup_YYYYMMDD_HHMMSS.json` - Manual backups

## 💾 What Data is Backed Up

- ✅ **Users**: All user accounts and profiles
- ✅ **Meter Readings**: Electricity meter readings
- ✅ **Bills**: Electricity bills and payments
- ✅ **Rent Payments**: All rent payment records
- ✅ **Chat Messages**: Communication history
- ✅ **Notifications**: System notifications
- ✅ **System Settings**: App configuration

## 🔧 Manual Recovery (If Needed)

If automatic restore doesn't work:

1. **Check Logs**: Look for backup restoration messages
2. **Manual Restore**: Use admin panel to create/download backups
3. **File Upload**: Manually place backup files in app directory
4. **Restart App**: Trigger restoration on restart

## ⚠️ Important Notes

- **Security**: Backup files contain sensitive data - store securely
- **Regular Backups**: Create backups before major changes
- **Test Restore**: Periodically test the restore process
- **Multiple Copies**: Keep backups in multiple locations

## 🎯 Quick Deployment Checklist

- [ ] Run `python create_backup.py` 
- [ ] Verify backup files created
- [ ] Commit and push code changes
- [ ] Deploy to hosting platform
- [ ] Check logs for automatic restoration
- [ ] Verify users are restored in admin panel

## 🆘 Troubleshooting

### "No users found after deployment"
1. Check app logs for restoration messages
2. Verify backup files exist in repository
3. Check file permissions
4. Manually trigger restore via admin panel

### "Backup creation failed"
1. Ensure database exists (`instance/billing.db`)
2. Check file permissions
3. Verify sufficient disk space
4. Check Python installation

### "Users restored but missing data"
1. Check backup file completeness
2. Verify all required tables backed up
3. Check for database schema changes
4. Review restoration logs

## 📞 Support

If you encounter issues:
1. Check the app logs first
2. Verify backup files exist
3. Test locally before deploying
4. Review this guide thoroughly

---

**Remember**: Always create a backup before deployment to prevent data loss! 🔒
