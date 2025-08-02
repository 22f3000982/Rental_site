@echo off
title Google Drive Backup System
color 0A

echo.
echo ================================================
echo          🚀 RENTAL SITE BACKUP SYSTEM
echo ================================================
echo.
echo � Running Google Drive Backup...
echo.

python gdrive_backup.py

echo.
echo ================================================
echo             ✅ BACKUP COMPLETE
echo ================================================
echo.
    python gdrive_backup.py
    echo.
    echo ✅ Ready for deployment! You can now safely:
    echo    git add .
    echo    git commit -m "Deploy with latest backup"
    echo    git push origin master
) else if "%choice%"=="3" (
    echo.
    echo 📂 Listing all backups...
    python gdrive_backup.py
) else (
    echo ❌ Invalid choice
)

echo.
pause
