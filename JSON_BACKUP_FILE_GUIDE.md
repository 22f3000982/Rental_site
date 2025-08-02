# 📁 JSON Backup System - File Name & Path Guide

## 📝 File Name Format
The backup file will be automatically named:
```
rental_backup_YYYYMMDD_HHMMSS.json
```

### Examples:
- `rental_backup_20250802_143022.json` (Aug 2, 2025 at 2:30:22 PM)
- `rental_backup_20250801_095530.json` (Aug 1, 2025 at 9:55:30 AM)

## 📂 File Path Location
Place your backup file at:
```
backend/rental_backup_YYYYMMDD_HHMMSS.json
```

### ⚠️ Important: File Placement
✅ **CORRECT**: Place directly in `backend/` folder
```
/Rental_site/backend/rental_backup_20250802_143022.json
```

❌ **WRONG**: Don't place in subfolders
```
/Rental_site/backend/json_backups/rental_backup_20250802_143022.json  ❌
/Rental_site/rental_backup_20250802_143022.json                        ❌
```

## 🔄 Complete Workflow

### Before Deployment:
1. Create backup from admin panel → Downloads file
2. Copy file to your local `backend/` folder
3. Add to git: `git add .`
4. Commit: `git commit -m "Add backup file"`
5. Push: `git push`

### After Deployment:
1. Go to admin panel → JSON Backup section
2. Click "Restore from JSON"
3. All users and data restored!
4. (Optional) Remove backup file from backend folder

## 💡 Pro Tips
- The system automatically detects any `rental_backup_*.json` file in the backend folder
- You can have multiple backup files - the system will list them all
- Keep backup files safe - they contain all your user data!
- The file format is human-readable JSON - you can even view/edit if needed

**Ready to use!** 🚀
