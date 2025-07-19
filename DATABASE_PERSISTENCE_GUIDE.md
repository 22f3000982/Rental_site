# Database Persistence Solutions

## Problem
When pushing to GitHub, registered users get lost because the SQLite database file (`readings.db`) is not tracked by Git (which is correct for security).

## Solutions

### Option 1: Use Production Database (Recommended)
1. **PostgreSQL** (for Railway, Heroku, etc.)
2. **MySQL** (for shared hosting)
3. **SQLite with persistent storage** (for development)

### Option 2: Database Migration/Backup System
1. Create database backup before push
2. Restore database after deployment
3. Use environment-based configuration

### Option 3: Database Initialization Script
1. Automatically create admin user on first run
2. Seed essential data on deployment

## Implementation Steps

### Step 1: Environment Configuration
```bash
# Development (.env)
DATABASE_URL=sqlite:///readings.db

# Production (.env.production)
DATABASE_URL=postgresql://user:password@host:port/database_name
```

### Step 2: Database Migration
```python
# Create database backup
python -c "
import sqlite3
import json
conn = sqlite3.connect('instance/readings.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM user')
users = cursor.fetchall()
with open('user_backup.json', 'w') as f:
    json.dump(users, f)
"
```

### Step 3: Auto-Initialize Database
```python
@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin if none exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com')
        admin.password_hash = generate_password_hash('admin123')
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
```

## Quick Fix for Development
1. Backup current database
2. Add database initialization
3. Use persistent volume for deployment
