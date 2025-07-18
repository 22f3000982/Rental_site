#!/bin/bash

# Rental Management System Installation Script

echo "🏠 Setting up Rental Management System..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # macOS/Linux
    source venv/bin/activate
fi

# Navigate to backend directory
cd backend

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configurations before running the app"
fi

# Initialize database
echo "🗄️ Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized successfully')"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To start the application:"
echo "1. Edit backend/.env file with your configurations"
echo "2. Run: cd backend && python app.py"
echo "3. Open your browser to http://localhost:5000"
echo ""
echo "Default admin credentials:"
echo "Email: ashraj77777@gmail.com"
echo "Password: 4129"
