@echo off
REM Rental Management System Installation Script for Windows

echo 🏠 Setting up Rental Management System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Navigate to backend directory
cd backend

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo ⚙️ Creating environment configuration...
    copy .env.example .env
    echo ✅ Please edit .env file with your configurations before running the app
)

REM Initialize database
echo 🗄️ Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized successfully')"

echo.
echo 🎉 Installation complete!
echo.
echo To start the application:
echo 1. Edit backend\.env file with your configurations
echo 2. Run: cd backend ^&^& python app.py
echo 3. Open your browser to http://localhost:5000
echo.
echo Default admin credentials:
echo Email: ashraj77777@gmail.com
echo Password: 4129
echo.
pause
