@echo off
title Rental Site + WhatsApp Backup (All-in-One)
color 0A

echo.
echo ======================================================================
echo          🚀 RENTAL SITE + WHATSAPP-STYLE BACKUP
echo ======================================================================
echo.
echo 🌐 Starting your rental site on: http://localhost:5000
echo 📱 Starting WhatsApp-style backup monitoring
echo ⏰ Automatic backups: Daily + Weekly + Instant
echo ☁️ Cloud storage: Google Drive
echo.
echo 💡 ONE PROCESS - NO NEED FOR MULTIPLE TERMINALS!
echo.
echo Press Ctrl+C to stop everything
echo.

python run_site_with_backup.py

echo.
echo ======================================================================
echo             ✅ RENTAL SITE + BACKUP STOPPED
echo ======================================================================
echo.
pause
