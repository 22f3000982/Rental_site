@echo off
echo 🚀 Preparing backup file for deployment...
echo.

REM Check if backup file exists in downloads or current directory
if exist "latest_backup.db" (
    echo ✅ Found latest_backup.db in current directory
    goto :copy_backup
)

if exist "%USERPROFILE%\Downloads\latest_backup.db" (
    echo ✅ Found latest_backup.db in Downloads folder
    copy "%USERPROFILE%\Downloads\latest_backup.db" "latest_backup.db"
    echo 📁 Copied from Downloads to current directory
    goto :copy_backup
)

echo ❌ latest_backup.db not found!
echo.
echo 📥 Please download your backup file first:
echo    1. Go to your admin panel
echo    2. Click "Open Database Backup"
echo    3. Click "Create New Backup"
echo    4. Click "Download" next to the backup file
echo    5. Save it as "latest_backup.db"
echo    6. Run this script again
echo.
pause
exit /b 1

:copy_backup
REM Create simple_backups directory in backend folder
if not exist "backend\simple_backups" (
    mkdir "backend\simple_backups"
    echo 📁 Created backend\simple_backups directory
)

REM Copy backup file to the correct location
copy "latest_backup.db" "backend\simple_backups\latest_backup.db"
echo ✅ Backup file copied to backend\simple_backups\latest_backup.db

echo.
echo 🎉 Ready for deployment!
echo.
echo Next steps:
echo 1. Push your code to git (the backup file will be included)
echo 2. Deploy your site
echo 3. The system will automatically restore your backup on startup!
echo.
pause
