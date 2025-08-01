# Database Persistence Guide for Render Deployment

## Problem
When deploying to Render, user data (renters who registered) gets lost because:
1. SQLite database files are ephemeral and get reset on each deployment
2. The filesystem is not persistent across deployments

## 🚀 QUICK SOLUTION (Before Your Next Push)

### Step 1: Create Backup Before Pushing
```bash
cd backend
python create_backup.py
```
This creates `current_users_backup.json` with all registered users.

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Update with data persistence fixes"
git push origin main
```

### Step 3: Your App Will Auto-Restore!
The app now automatically checks for backup files on startup and restores users if the database is empty.

## 💾 PERMANENT SOLUTION: PostgreSQL Database

### Step 1: Create PostgreSQL Database on Render
1. Go to your Render Dashboard: https://dashboard.render.com
2. Click "New" → "PostgreSQL"
3. Name: `rental-site-database`
4. Region: Same as your web service
5. Plan: Free
6. Click "Create Database"

### Step 2: Update Environment Variables
1. Go to your Web Service on Render
2. Go to "Environment" tab
3. Add this variable:
   ```
   Name: DATABASE_URL
   Value: [Copy the "External Database URL" from your PostgreSQL service]
   ```
   Example: `postgresql://user:pass@host:5432/database`

### Step 3: Deploy
Your code is already PostgreSQL-ready! Just redeploy and your data will persist.

## 🔄 Backup System Features

### Automatic Backup Detection
The app now checks these backup files in order:
1. `current_users_backup.json` (latest)
2. `pre_deploy_backup_20250719_125842.json` 
3. `pre_deploy_backup_20250719_125821.json`

### Manual Backup Creation
```bash
cd backend
python create_backup.py
```

### Full Database Backup
```bash
cd backend
python database_backup.py
```

## 📋 Deployment Checklist

**Before Every Deploy:**
- [ ] Run `python create_backup.py` to backup current users
- [ ] Commit and push the backup file
- [ ] Deploy to Render
- [ ] Verify users are restored after deployment

**One-Time Setup (Recommended):**
- [ ] Create PostgreSQL database on Render
- [ ] Update DATABASE_URL environment variable
- [ ] Redeploy once
- [ ] All future deployments will preserve data automatically!

## 🛡️ Data Safety Features Added

1. **Non-destructive Database Init**: `db.create_all()` only creates missing tables
2. **Smart User Detection**: Checks if database is empty before restoring
3. **Multiple Backup Sources**: Tries multiple backup files
4. **Error Handling**: Graceful fallback if restore fails
5. **Duplicate Prevention**: Won't restore users that already exist

## 🔍 Verification

After deployment, check:
1. Login with existing user accounts
2. Verify user data in admin panel
3. Check that new registrations still work

Your registered users should now persist across all deployments! 🎉
