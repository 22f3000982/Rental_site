@echo off
echo Creating database backup before deployment...
echo =============================================

python create_backup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Backup completed successfully!
    echo You can now safely deploy your application.
    echo.
    pause
) else (
    echo.
    echo ❌ Backup failed! Please check the errors above.
    echo.
    pause
    exit /b 1
)
