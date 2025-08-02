@echo off
title WhatsApp-Style Google Drive Backup
color 0B

echo.
echo ========================================================
echo          📱 WHATSAPP-STYLE BACKUP SYSTEM
echo ========================================================
echo.
echo 🔄 Starting automatic backup monitoring...
echo 📊 Like WhatsApp: Continuous backup to Google Drive
echo ⏰ Monitors changes and uploads automatically
echo.
echo Press Ctrl+C to stop the backup system
echo.

python auto_gdrive_backup.py

echo.
echo ========================================================
echo             ✅ BACKUP SYSTEM STOPPED
echo ========================================================
echo.
pause
