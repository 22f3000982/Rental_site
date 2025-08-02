@echo off
title Rental Site with JSON Backup
color 0A

echo.
echo ======================================================================
echo          🚀 RENTAL SITE WITH JSON BACKUP SYSTEM
echo ======================================================================
echo.
echo 🌐 Starting your rental site with backup system
echo 📁 JSON Backup: Download/Upload files manually
echo 📱 Simple Backup: WhatsApp-style Google Drive (if configured)
echo.
echo 💡 Access Points:
echo    • JSON Backup: http://localhost:5000/admin/json_backup
echo    • Simple Backup: http://localhost:5000/admin/simple_backup
echo    • Admin Dashboard: http://localhost:5000/admin/dashboard
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
python app.py

echo.
echo ======================================================================
echo             ✅ RENTAL SITE STOPPED
echo ======================================================================
echo.
pause
