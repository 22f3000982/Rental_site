# Deployment Guide

## Local Development

### Quick Setup (Recommended)

**For Windows:**
```bash
# Run the installation script
install.bat
```

**For macOS/Linux:**
```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

### Manual Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/22f3000982/Rental_site.git
   cd Rental_site
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

## Production Deployment

### Using Gunicorn (Recommended)

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Using Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app
   COPY backend/ .
   
   RUN pip install -r requirements.txt
   
   EXPOSE 5000
   
   CMD ["python", "app.py"]
   ```

2. **Build and run**
   ```bash
   docker build -t rental-system .
   docker run -p 5000:5000 rental-system
   ```

### Environment Variables for Production

```env
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@localhost/rental_db
UPLOAD_FOLDER=/app/uploads
```

## Security Considerations

1. **Change default admin credentials immediately**
2. **Use strong SECRET_KEY in production**
3. **Use PostgreSQL instead of SQLite for production**
4. **Set up proper file permissions for uploads**
5. **Use HTTPS in production**
6. **Regular database backups**

## File Structure for Deployment

```
├── backend/
│   ├── app.py              # Main application
│   ├── models.py           # Database models
│   ├── forms.py            # Forms
│   ├── requirements.txt    # Dependencies
│   ├── .env               # Environment config (create from .env.example)
│   ├── templates/         # HTML templates
│   ├── static/           # CSS, JS, images
│   └── instance/         # Database files (auto-created)
├── uploads/              # User uploads (auto-created)
├── README.md            # Documentation
└── .gitignore          # Git ignore rules
```

## Backup Strategy

### Database Backup
```bash
# SQLite backup
cp backend/instance/billing.db backup/billing_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump rental_db > backup/rental_db_$(date +%Y%m%d).sql
```

### File Backup
```bash
# Backup uploads
tar -czf backup/uploads_$(date +%Y%m%d).tar.gz uploads/
```

## Monitoring

### Log Files
- Application logs: Check Flask output
- Error logs: Monitor for exceptions
- Access logs: Track user activity

### Health Checks
- Database connectivity
- File system permissions
- Memory usage
- Disk space

## Troubleshooting

### Common Issues

1. **Database not found**
   - Run database initialization script
   - Check file permissions

2. **Upload errors**
   - Verify upload directory exists
   - Check file permissions
   - Validate file size limits

3. **Import errors**
   - Verify virtual environment is activated
   - Check all dependencies are installed
   - Validate Python version (3.8+)

### Performance Optimization

1. **Database indexing**
2. **File compression**
3. **Caching static files**
4. **Load balancing for high traffic**
