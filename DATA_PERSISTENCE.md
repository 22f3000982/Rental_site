# Data Persistence Guide

## 🔄 **Will User Data Persist After Code Updates?**

**YES** - User data will persist if you follow proper deployment practices!

## ✅ **What Persists (Safe)**
- User registrations
- Payment records
- Uploaded receipts and documents
- System settings
- All database content

## ❌ **What Gets Updated (Changes)**
- Application code (app.py, templates, etc.)
- CSS styles and UI changes
- New features and bug fixes
- Static files

## 📊 **Database vs Code Separation**

### **Database (Persistent Storage)**
```
Users, Payments, Documents, Settings
     ↓
External Database (PostgreSQL/MySQL)
     ↓
✅ NEVER DELETED during code updates
```

### **Application Code (Updates)**
```
app.py, CSS, HTML templates
     ↓
GitHub Repository
     ↓
🔄 UPDATED when you push changes
```

## 🛡️ **How to Ensure Data Persistence**

### **1. Use External Database (NOT SQLite)**
```python
# ❌ BAD - File-based database (gets deleted)
DATABASE_URL=sqlite:///billing.db

# ✅ GOOD - External database (persists)
DATABASE_URL=postgresql://user:pass@host:5432/rental_db
```

### **2. Separate File Storage**
```python
# ❌ BAD - Files in app directory
UPLOAD_FOLDER = 'uploads'

# ✅ GOOD - External file storage
UPLOAD_FOLDER = '/app/persistent_storage/uploads'
# Or use cloud storage (AWS S3, Google Cloud)
```

### **3. Environment Variables**
```bash
# Keep sensitive data in environment variables
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
UPLOAD_FOLDER=/persistent/uploads
```

## 🚀 **Recommended Production Setup**

### **Railway Deployment (Easiest)**
1. **Database**: Railway PostgreSQL (persistent)
2. **Files**: Railway volumes (persistent)
3. **Code**: Auto-deploy from GitHub

### **Setup Steps:**
```bash
# 1. Create railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python backend/app.py"
  }
}

# 2. Add environment variables in Railway:
DATABASE_URL=postgresql://...
SECRET_KEY=random-secret-key
UPLOAD_FOLDER=/app/uploads
```

## 📝 **Update Workflow (Safe)**

### **Typical Update Process:**
1. **Make changes** to CSS/code locally
2. **Test** changes work correctly
3. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Update CSS styling"
   git push origin master
   ```
4. **Automatic deployment** (Railway/Render)
5. **User data remains intact** ✅

### **What Happens During Update:**
- ✅ Database stays connected
- ✅ User accounts remain active
- ✅ Payment history preserved
- ✅ Uploaded files stay accessible
- 🔄 New CSS/features go live

## ⚠️ **What Could Cause Data Loss**

### **Dangerous Actions:**
1. **Deleting the database** manually
2. **Changing database URL** without migration
3. **Using SQLite** in production (file gets overwritten)
4. **Deleting uploaded files** directory

### **Safe Actions:**
- Updating Python code
- Changing CSS/HTML
- Adding new features
- Fixing bugs
- Pushing to GitHub

## 🔧 **Migration Strategy**

### **For Database Schema Changes:**
```python
# If you add new columns/tables
def migrate_database():
    with app.app_context():
        # Add new columns safely
        db.engine.execute("ALTER TABLE users ADD COLUMN new_field VARCHAR(255)")
        db.create_all()  # Create new tables
```

### **For File Structure Changes:**
```python
# Move files safely during deployment
import shutil
old_path = '/app/old_uploads'
new_path = '/app/new_uploads'
if os.path.exists(old_path):
    shutil.move(old_path, new_path)
```

## 📊 **Backup Strategy**

### **Automated Backups:**
```bash
# Database backup (daily)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# File backup (daily)
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /app/uploads/
```

### **Railway Backup:**
- Database snapshots available
- Automatic backups enabled
- Point-in-time recovery

## 🎯 **Best Practices Summary**

1. **✅ Use PostgreSQL** (not SQLite) in production
2. **✅ Store files** in persistent volumes or cloud storage
3. **✅ Use environment variables** for configuration
4. **✅ Test updates** in development first
5. **✅ Set up automated backups**
6. **✅ Monitor deployments** for issues

## 🚨 **Emergency Recovery**

### **If Data Gets Lost:**
1. **Check backup files**
2. **Restore from database snapshot**
3. **Contact hosting provider support**
4. **Use version control** to rollback code

### **Prevention:**
- Regular automated backups
- Staging environment for testing
- Database replication
- File storage redundancy
