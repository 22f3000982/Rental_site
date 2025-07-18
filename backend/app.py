from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
import calendar
from decimal import Decimal
from dotenv import load_dotenv
from models import db, User, MeterReading, ElectricityBill, RentPayment, SystemSettings, Document, Notification, ChatMessage, UserProfile
from forms import (RegistrationForm, LoginForm, MeterReadingForm, RentAssignmentForm, 
                  SystemSettingsForm, PaymentForm, PasswordResetForm, 
                  NewPasswordForm, EditRenterForm, ChatMessageForm, UserProfileForm, 
                  DocumentUploadForm, DocumentVerificationForm, ProfilePictureForm)
import json
import io
import zipfile

# Optional imports for Excel functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///billing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Make calendar available in templates
app.jinja_env.globals['calendar'] = calendar

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin_user():
    """Create default admin user"""
    admin = User.query.filter_by(email='ashraj77777@gmail.com').first()
    if not admin:
        # Get admin password from environment variable, default to simple password
        admin_password = os.environ.get('ADMIN_PASSWORD', '4129')
        
        admin = User(
            username='admin',
            email='ashraj77777@gmail.com',
            password_hash=generate_password_hash(admin_password),
            password_plain=admin_password,
            is_admin=True,
            is_approved=True  # Admin is auto-approved
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user initialized successfully")

def migrate_database():
    """Migrate database to add new columns and tables"""
    try:
        with app.app_context():
            # For PostgreSQL, we just ensure all tables exist
            # SQLAlchemy will handle the schema creation
            print("Running database migration for PostgreSQL...")
            
            # The db.create_all() already handles creating all tables
            # with the correct schema from models.py
            
            print("Database migration completed successfully")
    except Exception as e:
        print(f"Database migration error: {e}")

def create_default_settings():
    """Create default system settings"""
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings(
            electricity_rate=8.0,
            fixed_charge=0.0,
            rent_due_date=5
        )
        db.session.add(settings)
        db.session.commit()
        print("Default settings created")
    else:
        # Update existing settings to ensure correct values
        settings.electricity_rate = 8.0
        settings.fixed_charge = 0.0
        db.session.commit()
        print("Settings updated to correct values")

def calculate_electricity_bill(meter_reading):
    """Calculate electricity bill based on meter reading"""
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings(electricity_rate=8.0, fixed_charge=0.0)
        db.session.add(settings)
        db.session.commit()
    
    total_amount = (meter_reading.units_consumed * settings.electricity_rate) + settings.fixed_charge
    
    return ElectricityBill(
        renter_id=meter_reading.renter_id,
        meter_reading_id=meter_reading.id,
        units_consumed=meter_reading.units_consumed,
        rate_per_unit=settings.electricity_rate,
        fixed_charge=settings.fixed_charge,
        total_amount=total_amount,
        month=meter_reading.month,
        year=meter_reading.year
    )

def create_monthly_rent_payment(renter, month, year):
    """Create monthly rent payment record"""
    settings = SystemSettings.query.first()
    due_date = date(year, month, settings.rent_due_date if settings else 5)
    
    existing_payment = RentPayment.query.filter_by(
        renter_id=renter.id,
        month=month,
        year=year
    ).first()
    
    if not existing_payment:
        rent_payment = RentPayment(
            renter_id=renter.id,
            amount=renter.rent_amount,
            month=month,
            year=year,
            due_date=due_date
        )
        db.session.add(rent_payment)
        return rent_payment
    return existing_payment

# Initialize database tables and default data
def init_database():
    """Initialize database tables and create default data"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("Database tables created successfully")
            
            # Run migrations
            migrate_database()
            
            # Create default settings
            create_default_settings()
            
            # Create default admin user
            create_admin_user()
            
            print("Database initialization completed")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Call init_database when the app starts
init_database()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('renter_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('register.html', form=form)
        
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            password_plain=form.password.data,  # Store plain password (as per requirement)
            phone=form.phone.data,
            room_number=form.room_number.data,
            rent_amount=0.0  # Will be set by admin
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Your account is pending admin approval. You will be able to login once approved.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'error')
                return render_template('login.html', form=form)
            
            if not user.is_admin and not user.is_approved:
                flash('Your account is pending admin approval. Please wait for approval.', 'error')
                return render_template('login.html', form=form)
            
            login_user(user, remember=form.remember.data)
            
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('renter_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# RENTER ROUTES
@app.route('/renter/dashboard')
@login_required
def renter_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get current month data
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get rent payment for current month
    rent_payment = RentPayment.query.filter_by(
        renter_id=current_user.id,
        month=current_month,
        year=current_year
    ).first()
    
    # Get electricity bill for current month
    electricity_bill = ElectricityBill.query.filter_by(
        renter_id=current_user.id,
        month=current_month,
        year=current_year
    ).first()
    
    # Get payment history
    rent_payments = RentPayment.query.filter_by(renter_id=current_user.id).order_by(RentPayment.year.desc(), RentPayment.month.desc()).limit(12).all()
    electricity_bills = ElectricityBill.query.filter_by(renter_id=current_user.id).order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).limit(12).all()
    
    # Get notifications
    notifications = Notification.query.filter_by(renter_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Calculate total due
    total_due = Decimal('0')
    if rent_payment and not rent_payment.is_paid:
        total_due += rent_payment.amount
    if electricity_bill and not electricity_bill.is_paid:
        total_due += electricity_bill.remaining_amount
    
    return render_template('renter_dashboard.html',
                         rent_payment=rent_payment,
                         electricity_bill=electricity_bill,
                         rent_payments=rent_payments,
                         electricity_bills=electricity_bills,
                         notifications=notifications,
                         total_due=total_due,
                         current_month=current_month,
                         current_year=current_year)

@app.route('/renter/pay/<payment_type>/<int:payment_id>')
@login_required
def pay_bill(payment_type, payment_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if payment_type == 'rent':
        payment = RentPayment.query.get_or_404(payment_id)
        if payment.renter_id != current_user.id:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('renter_dashboard'))
    elif payment_type == 'electricity':
        payment = ElectricityBill.query.get_or_404(payment_id)
        if payment.renter_id != current_user.id:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('renter_dashboard'))
    
    # Use static QR code image
    return render_template('payment.html', 
                         payment=payment, 
                         payment_type=payment_type)

@app.route('/renter/confirm_payment/<payment_type>/<int:payment_id>', methods=['POST'])
@login_required
def confirm_payment(payment_type, payment_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if payment_type == 'rent':
        payment = RentPayment.query.get_or_404(payment_id)
        if payment.renter_id != current_user.id:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('renter_dashboard'))
    elif payment_type == 'electricity':
        payment = ElectricityBill.query.get_or_404(payment_id)
        if payment.renter_id != current_user.id:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('renter_dashboard'))
    
    # Handle receipt upload
    receipt_file = request.files.get('payment_receipt')
    receipt_filename = None
    
    if receipt_file and receipt_file.filename:
        # Validate file size (5MB limit)
        receipt_file.seek(0, 2)  # Seek to end
        file_size = receipt_file.tell()
        receipt_file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            flash('Receipt file size must be less than 5MB.', 'error')
            return redirect(url_for('pay_bill', payment_type=payment_type, payment_id=payment_id))
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
        file_ext = os.path.splitext(receipt_file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            flash('Invalid file type. Please upload JPG, PNG, or PDF files only.', 'error')
            return redirect(url_for('pay_bill', payment_type=payment_type, payment_id=payment_id))
        
        # Save the receipt file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        receipt_filename = f"receipt_{payment_type}_{payment_id}_{timestamp}{file_ext}"
        receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(os.path.dirname(receipt_path), exist_ok=True)
        receipt_file.save(receipt_path)
        
        # Store relative path for database
        receipt_filename = f"uploads/{receipt_filename}"
    else:
        flash('Payment receipt is required.', 'error')
        return redirect(url_for('pay_bill', payment_type=payment_type, payment_id=payment_id))
    
    # Mark as pending for admin approval
    if payment_type == 'rent':
        payment.payment_status = 'pending'
        payment.payment_receipt = receipt_filename
    elif payment_type == 'electricity':
        payment.payment_status = 'pending'
        payment.payment_receipt = receipt_filename
    
    payment.payment_date = datetime.now()
    payment.payment_method = request.form.get('payment_method', 'upi')
    payment.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Save transaction notes if provided
    transaction_notes = request.form.get('transaction_notes', '').strip()
    if transaction_notes:
        if payment_type == 'rent':
            payment.verification_notes = f"User notes: {transaction_notes}"
        elif payment_type == 'electricity':
            payment.verification_notes = f"User notes: {transaction_notes}"
    
    db.session.commit()
    flash('Payment receipt uploaded successfully! Your payment is now pending admin approval.', 'success')
    
    return redirect(url_for('renter_dashboard'))

@app.route('/static/qr_code.jpeg')
def serve_qr_code():
    """Serve the static QR code image"""
    return send_file('../qr_code.jpeg', mimetype='image/jpeg')

@app.route('/uploads/<filename>')
@login_required
def serve_uploaded_file(filename):
    """Serve uploaded files (receipts, documents, etc.)"""
    if not current_user.is_admin:
        # For non-admin users, ensure they can only access their own files
        # This is a basic security check - you might want to add more validation
        flash('Access denied.', 'error')
        return redirect(url_for('renter_dashboard'))
    
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            flash('File not found.', 'error')
            return redirect(url_for('admin_pending_payments'))
        
        # Determine MIME type based on file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ['.jpg', '.jpeg']:
            mimetype = 'image/jpeg'
        elif file_ext == '.png':
            mimetype = 'image/png'
        elif file_ext == '.pdf':
            mimetype = 'application/pdf'
        else:
            mimetype = 'application/octet-stream'
        
        return send_file(file_path, mimetype=mimetype)
    except Exception as e:
        flash('Error loading file.', 'error')
        return redirect(url_for('admin_pending_payments'))

@app.route('/renter/notifications')
@login_required
def renter_notifications():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    notifications = Notification.query.filter_by(renter_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark as read
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    
    return render_template('renter_notifications.html', notifications=notifications)

@app.route('/renter/reading_history')
@login_required
def renter_reading_history():
    """View all meter readings for the current user"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get all readings for the current user, ordered by date desc
    readings = MeterReading.query.filter_by(renter_id=current_user.id)\
        .order_by(MeterReading.year.desc(), MeterReading.month.desc()).all()
    
    return render_template('renter_reading_history.html', 
                         readings=readings)

@app.route('/renter/payment_receipts')
@login_required
def renter_payment_receipts():
    """View all payment receipts and data for the current user"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get filter parameters
    selected_year = request.args.get('year', type=int)
    selected_status = request.args.get('status', '')
    selected_type = request.args.get('payment_type', '')
    
    # Get all electricity bills
    electricity_query = ElectricityBill.query.filter_by(renter_id=current_user.id)
    
    # Get all rent payments
    rent_query = RentPayment.query.filter_by(renter_id=current_user.id)
    
    # Apply filters
    if selected_year:
        electricity_query = electricity_query.filter(ElectricityBill.year == selected_year)
        rent_query = rent_query.filter(RentPayment.year == selected_year)
    
    if selected_status:
        if selected_status == 'approved':
            electricity_query = electricity_query.filter(ElectricityBill.payment_status == 'approved')
            rent_query = rent_query.filter(RentPayment.is_paid == True)
        elif selected_status == 'pending':
            electricity_query = electricity_query.filter(ElectricityBill.payment_status == 'pending')
            rent_query = rent_query.filter(RentPayment.is_paid == False)
        elif selected_status == 'rejected':
            electricity_query = electricity_query.filter(ElectricityBill.payment_status == 'rejected')
    
    # Get the data
    electricity_bills = electricity_query.order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
    rent_payments = rent_query.order_by(RentPayment.year.desc(), RentPayment.month.desc()).all()
    
    # Combine and filter by type
    payments = []
    if selected_type == 'electricity':
        payments = electricity_bills
    elif selected_type == 'rent':
        payments = rent_payments
    else:
        payments = electricity_bills + rent_payments
        # Sort by payment date
        payments.sort(key=lambda x: x.payment_date if x.payment_date else datetime.min, reverse=True)
    
    # Calculate statistics
    total_amount = 0
    approved_count = 0
    pending_count = 0
    
    for payment in payments:
        if hasattr(payment, 'amount_paid') and payment.amount_paid:
            total_amount += float(payment.amount_paid)
        elif hasattr(payment, 'amount') and payment.amount:
            total_amount += float(payment.amount)
        
        if (hasattr(payment, 'payment_status') and payment.payment_status == 'approved') or \
           (hasattr(payment, 'is_paid') and payment.is_paid):
            approved_count += 1
        elif (hasattr(payment, 'payment_status') and payment.payment_status == 'pending') or \
             (hasattr(payment, 'is_paid') and not payment.is_paid):
            pending_count += 1
    
    # Get unique years for filter
    years = sorted(set([p.year for p in payments]), reverse=True)
    
    return render_template('renter_payment_receipts.html', 
                         payments=payments,
                         years=years,
                         selected_year=selected_year,
                         selected_status=selected_status,
                         selected_type=selected_type,
                         total_amount=total_amount,
                         approved_count=approved_count,
                         pending_count=pending_count)

@app.route('/renter/payment_history_table')
@login_required
def renter_payment_history_table():
    """Renter view for payment history in tabular format"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get filter parameters
    year_filter = request.args.get('year', type=int)
    month_filter = request.args.get('month', type=int)
    format_type = request.args.get('format', '').lower()
    
    # Get current user's rent payments that are paid
    rent_query = RentPayment.query.filter_by(renter_id=current_user.id, is_paid=True)
    electricity_query = ElectricityBill.query.filter_by(renter_id=current_user.id, is_paid=True)
    
    # Apply filters
    if year_filter:
        rent_query = rent_query.filter(RentPayment.year == year_filter)
        electricity_query = electricity_query.filter(ElectricityBill.year == year_filter)
    
    if month_filter:
        rent_query = rent_query.filter(RentPayment.month == month_filter)
        electricity_query = electricity_query.filter(ElectricityBill.month == month_filter)
    
    # Get the data
    rent_payments = rent_query.order_by(RentPayment.payment_date.desc()).all()
    electricity_bills = electricity_query.order_by(ElectricityBill.payment_date.desc()).all()
    
    # Combine payments by date for table format
    payment_records = []
    
    # Process rent payments
    for rent in rent_payments:
        # Find corresponding electricity bill for same month/year
        electricity_bill = None
        for bill in electricity_bills:
            if (bill.month == rent.month and bill.year == rent.year):
                electricity_bill = bill
                break
        
        # Create combined record
        total_received = float(rent.amount or 0)
        electric_amount = 0
        units_consumed = 0
        
        if electricity_bill:
            electric_amount = float(electricity_bill.amount_paid or electricity_bill.total_amount or 0)
            units_consumed = float(electricity_bill.units_consumed or 0)
            total_received += electric_amount
        
        payment_records.append({
            'date': rent.payment_date.strftime('%d-%m-%Y') if rent.payment_date else f"{rent.month:02d}-{rent.year}",
            'total_received': total_received,
            'flat_rent': float(rent.amount or 0),
            'electric_bill': electric_amount,
            'units_consumed': units_consumed,
            'month': f"{calendar.month_name[rent.month]} {rent.year}",
            'payment_method': rent.payment_method or 'Cash',
            'payment_date': rent.payment_date,
            'rent_id': rent.id,
            'electricity_id': electricity_bill.id if electricity_bill else None
        })
    
    # Add electricity bills that don't have corresponding rent payments
    for bill in electricity_bills:
        # Check if this bill is already included in rent payments
        already_included = False
        for record in payment_records:
            if record['electricity_id'] == bill.id:
                already_included = True
                break
        
        if not already_included:
            electric_amount = float(bill.amount_paid or bill.total_amount or 0)
            payment_records.append({
                'date': bill.payment_date.strftime('%d-%m-%Y') if bill.payment_date else f"{bill.month:02d}-{bill.year}",
                'total_received': electric_amount,
                'flat_rent': 0,
                'electric_bill': electric_amount,
                'units_consumed': float(bill.units_consumed or 0),
                'month': f"{calendar.month_name[bill.month]} {bill.year}",
                'payment_method': bill.payment_method or 'Cash',
                'payment_date': bill.payment_date,
                'rent_id': None,
                'electricity_id': bill.id
            })
    
    # Sort by payment date (most recent first)
    payment_records.sort(key=lambda x: x['payment_date'] or datetime.min, reverse=True)
    
    # Calculate totals
    total_amount = sum([record['total_received'] for record in payment_records])
    total_rent = sum([record['flat_rent'] for record in payment_records])
    total_electricity = sum([record['electric_bill'] for record in payment_records])
    total_units = sum([record['units_consumed'] for record in payment_records])
    
    # Get filter options (years from user's own data)
    years = sorted(set([r.year for r in rent_payments] + [b.year for b in electricity_bills]), reverse=True)
    
    # Handle export requests
    if format_type == 'excel':
        return export_renter_payment_table_excel(payment_records, current_user, year_filter, month_filter)
    elif format_type == 'pdf':
        return export_renter_payment_table_pdf(payment_records, current_user, year_filter, month_filter)
    
    return render_template('renter_payment_history_table.html',
                         payment_records=payment_records,
                         total_amount=total_amount,
                         total_rent=total_rent,
                         total_electricity=total_electricity,
                         total_units=total_units,
                         years=years,
                         year_filter=year_filter,
                         month_filter=month_filter,
                         current_user=current_user)

@app.route('/download/reading_history')
@login_required
def download_reading_history():
    """Download reading history as PDF or Excel"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    format_type = request.args.get('format', 'pdf')
    
    # Get all readings for the current user
    readings = MeterReading.query.filter_by(renter_id=current_user.id)\
        .order_by(MeterReading.year.desc(), MeterReading.month.desc()).all()
    
    if format_type == 'excel':
        return generate_reading_excel(readings, current_user)
    else:
        return generate_reading_pdf(readings, current_user)

@app.route('/download/payment_receipts')
@login_required
def download_payment_receipts():
    """Download all payment receipts as ZIP file"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    return generate_receipts_zip(current_user)

@app.route('/download/payment_data')
@login_required
def download_payment_data():
    """Download payment data as Excel"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    return generate_payment_data_excel(current_user)

@app.route('/download/payment_receipt/<int:payment_id>/<payment_type>')
@login_required
def download_payment_receipt(payment_id, payment_type):
    """Download individual payment receipt"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if payment_type == 'ElectricityBill':
        payment = ElectricityBill.query.get_or_404(payment_id)
    else:
        payment = RentPayment.query.get_or_404(payment_id)
    
    if payment.renter_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('renter_dashboard'))
    

    return generate_individual_receipt(payment, payment_type)

# --- Helper function to generate individual PDF receipt ---
def generate_individual_receipt(payment, payment_type):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "Payment Receipt")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Payment ID: {getattr(payment, 'id', 'N/A')}")
    c.drawString(50, height - 120, f"Payment Type: {payment_type}")
    c.drawString(50, height - 140, f"Amount: {getattr(payment, 'amount', getattr(payment, 'total_received', 'N/A'))}")
    c.drawString(50, height - 160, f"Date: {getattr(payment, 'payment_date', getattr(payment, 'date', 'N/A'))}")
    c.drawString(50, height - 180, f"Renter: {getattr(payment, 'renter_name', getattr(payment, 'renter_id', 'N/A'))}")
    c.drawString(50, height - 200, f"Description: {getattr(payment, 'description', '')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"receipt_{getattr(payment, 'id', 'N/A')}.pdf",
        mimetype="application/pdf"
    )

# --- Helper functions for export functionality ---
def generate_payment_data_excel(user):
    """Generate Excel file with all payment data for a user"""
    if not PANDAS_AVAILABLE or not OPENPYXL_AVAILABLE:
        flash('Excel export functionality is not available. Please use PDF export instead.', 'warning')
        return redirect(url_for('renter_dashboard'))
    
    buffer = io.BytesIO()
    
    # Get user's payment data
    rent_payments = RentPayment.query.filter_by(renter_id=user.id, is_paid=True).order_by(RentPayment.payment_date.desc()).all()
    electricity_bills = ElectricityBill.query.filter_by(renter_id=user.id, is_paid=True).order_by(ElectricityBill.payment_date.desc()).all()
    
    # Create workbook with multiple sheets
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Rent payments sheet
        if rent_payments:
            rent_data = []
            for payment in rent_payments:
                rent_data.append({
                    'Date': payment.payment_date.strftime('%d-%m-%Y') if payment.payment_date else '',
                    'Month': f"{calendar.month_name[payment.month]} {payment.year}",
                    'Amount': payment.amount,
                    'Payment Method': payment.payment_method or 'Cash',
                    'Transaction ID': payment.transaction_id or '',
                    'Status': 'Paid' if payment.is_paid else 'Pending'
                })
            
            rent_df = pd.DataFrame(rent_data)
            rent_df.to_excel(writer, sheet_name='Rent Payments', index=False)
        
        # Electricity bills sheet
        if electricity_bills:
            electricity_data = []
            for bill in electricity_bills:
                electricity_data.append({
                    'Date': bill.payment_date.strftime('%d-%m-%Y') if bill.payment_date else '',
                    'Month': f"{calendar.month_name[bill.month]} {bill.year}",
                    'Units Consumed': bill.units_consumed,
                    'Rate per Unit': bill.rate_per_unit,
                    'Total Amount': bill.total_amount,
                    'Amount Paid': bill.amount_paid or bill.total_amount,
                    'Payment Method': bill.payment_method or 'Cash',
                    'Transaction ID': bill.transaction_id or '',
                    'Status': 'Paid' if bill.is_paid else 'Pending'
                })
            
            electricity_df = pd.DataFrame(electricity_data)
            electricity_df.to_excel(writer, sheet_name='Electricity Bills', index=False)
        
        # Summary sheet
        summary_data = {
            'Description': ['Total Rent Paid', 'Total Electricity Paid', 'Total Amount Paid'],
            'Amount': [
                sum([p.amount for p in rent_payments]),
                sum([b.amount_paid or b.total_amount for b in electricity_bills]),
                sum([p.amount for p in rent_payments]) + sum([b.amount_paid or b.total_amount for b in electricity_bills])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"payment_data_{user.username}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def generate_receipts_zip(user):
    """Generate ZIP file containing all payment receipts for a user"""
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add rent payment receipts
        rent_payments = RentPayment.query.filter_by(renter_id=user.id, is_paid=True).all()
        for payment in rent_payments:
            receipt_buffer = io.BytesIO()
            c = canvas.Canvas(receipt_buffer, pagesize=letter)
            width, height = letter
            
            # Create receipt content
            c.setFont("Helvetica-Bold", 16)
            c.drawString(200, height - 50, "Rent Payment Receipt")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 100, f"Receipt ID: RENT-{payment.id}")
            c.drawString(50, height - 120, f"Payment Date: {payment.payment_date.strftime('%d-%m-%Y') if payment.payment_date else 'N/A'}")
            c.drawString(50, height - 140, f"Month/Year: {calendar.month_name[payment.month]} {payment.year}")
            c.drawString(50, height - 160, f"Amount: ₹{payment.amount}")
            c.drawString(50, height - 180, f"Payment Method: {payment.payment_method or 'Cash'}")
            c.drawString(50, height - 200, f"Transaction ID: {payment.transaction_id or 'N/A'}")
            c.drawString(50, height - 220, f"Renter: {user.username}")
            
            c.showPage()
            c.save()
            receipt_buffer.seek(0)
            
            zip_file.writestr(f"rent_receipt_{payment.month:02d}_{payment.year}.pdf", receipt_buffer.getvalue())
        
        # Add electricity bill receipts
        electricity_bills = ElectricityBill.query.filter_by(renter_id=user.id, is_paid=True).all()
        for bill in electricity_bills:
            receipt_buffer = io.BytesIO()
            c = canvas.Canvas(receipt_buffer, pagesize=letter)
            width, height = letter
            
            # Create receipt content
            c.setFont("Helvetica-Bold", 16)
            c.drawString(200, height - 50, "Electricity Bill Receipt")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 100, f"Receipt ID: ELEC-{bill.id}")
            c.drawString(50, height - 120, f"Payment Date: {bill.payment_date.strftime('%d-%m-%Y') if bill.payment_date else 'N/A'}")
            c.drawString(50, height - 140, f"Month/Year: {calendar.month_name[bill.month]} {bill.year}")
            c.drawString(50, height - 160, f"Units Consumed: {bill.units_consumed}")
            c.drawString(50, height - 180, f"Rate per Unit: ₹{bill.rate_per_unit}")
            c.drawString(50, height - 200, f"Total Amount: ₹{bill.total_amount}")
            c.drawString(50, height - 220, f"Amount Paid: ₹{bill.amount_paid or bill.total_amount}")
            c.drawString(50, height - 240, f"Payment Method: {bill.payment_method or 'Cash'}")
            c.drawString(50, height - 260, f"Transaction ID: {bill.transaction_id or 'N/A'}")
            c.drawString(50, height - 280, f"Renter: {user.username}")
            
            c.showPage()
            c.save()
            receipt_buffer.seek(0)
            
            zip_file.writestr(f"electricity_receipt_{bill.month:02d}_{bill.year}.pdf", receipt_buffer.getvalue())
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"all_receipts_{user.username}.zip",
        mimetype="application/zip"
    )

def generate_reading_excel(readings, user):
    """Generate Excel file with meter readings"""
    if not PANDAS_AVAILABLE or not OPENPYXL_AVAILABLE:
        flash('Excel export functionality is not available. Please use PDF export instead.', 'warning')
        return redirect(url_for('renter_dashboard'))
    
    buffer = io.BytesIO()
    
    if readings:
        data = []
        for reading in readings:
            data.append({
                'Date': reading.reading_date.strftime('%d-%m-%Y') if reading.reading_date else '',
                'Month': f"{calendar.month_name[reading.month]} {reading.year}",
                'Previous Reading': reading.previous_reading,
                'Current Reading': reading.current_reading,
                'Units Consumed': reading.units_consumed,
                'Submitted By': reading.submitted_by or 'Admin'
            })
        
        df = pd.DataFrame(data)
        df.to_excel(buffer, index=False, engine='openpyxl')
    else:
        # Create empty Excel file
        df = pd.DataFrame({'Message': ['No meter readings found']})
        df.to_excel(buffer, index=False, engine='openpyxl')
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"meter_readings_{user.username}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def generate_reading_pdf(readings, user):
    """Generate PDF file with meter readings"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"Meter Reading History - {user.username}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    if readings:
        # Create table data
        data = [['Date', 'Month/Year', 'Previous', 'Current', 'Units Consumed']]
        
        for reading in readings:
            data.append([
                reading.reading_date.strftime('%d-%m-%Y') if reading.reading_date else 'N/A',
                f"{calendar.month_name[reading.month]} {reading.year}",
                str(reading.previous_reading),
                str(reading.current_reading),
                str(reading.units_consumed)
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("No meter readings found.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"meter_readings_{user.username}.pdf",
        mimetype="application/pdf"
    )

def export_renter_payment_table_excel(payment_records, user, year_filter=None, month_filter=None):
    """Export renter payment table to Excel"""
    if not PANDAS_AVAILABLE or not OPENPYXL_AVAILABLE:
        flash('Excel export functionality is not available. Please use PDF export instead.', 'warning')
        return redirect(url_for('renter_dashboard'))
    
    buffer = io.BytesIO()
    
    # Create DataFrame
    data = []
    for record in payment_records:
        data.append({
            'Date': record['date'],
            'Month': record['month'],
            'Total Received': record['total_received'],
            'Flat Rent': record['flat_rent'],
            'Electric Bill': record['electric_bill'],
            'Units Consumed': record['units_consumed'],
            'Payment Method': record['payment_method']
        })
    
    df = pd.DataFrame(data)
    
    # Add totals row
    totals_row = {
        'Date': 'TOTAL',
        'Month': '',
        'Total Received': sum([r['total_received'] for r in payment_records]),
        'Flat Rent': sum([r['flat_rent'] for r in payment_records]),
        'Electric Bill': sum([r['electric_bill'] for r in payment_records]),
        'Units Consumed': sum([r['units_consumed'] for r in payment_records]),
        'Payment Method': ''
    }
    df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)
    
    # Write to Excel
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    
    filename = f"payment_history_{user.username}"
    if year_filter:
        filename += f"_{year_filter}"
    if month_filter:
        filename += f"_{month_filter:02d}"
    filename += ".xlsx"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_renter_payment_table_pdf(payment_records, user, year_filter=None, month_filter=None):
    """Export renter payment table to PDF"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_text = f"Payment History - {user.username}"
    if year_filter:
        title_text += f" ({year_filter})"
    title = Paragraph(title_text, styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    if payment_records:
        # Create table data
        data = [['Date', 'Month', 'Total', 'Rent', 'Electric', 'Units', 'Method']]
        
        for record in payment_records:
            data.append([
                record['date'],
                record['month'],
                f"₹{record['total_received']:.2f}",
                f"₹{record['flat_rent']:.2f}",
                f"₹{record['electric_bill']:.2f}",
                f"{record['units_consumed']:.1f}",
                record['payment_method']
            ])
        
        # Add totals row
        totals = [
            'TOTAL',
            '',
            f"₹{sum([r['total_received'] for r in payment_records]):.2f}",
            f"₹{sum([r['flat_rent'] for r in payment_records]):.2f}",
            f"₹{sum([r['electric_bill'] for r in payment_records]):.2f}",
            f"{sum([r['units_consumed'] for r in payment_records]):.1f}",
            ''
        ]
        data.append(totals)
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("No payment records found.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"payment_history_{user.username}"
    if year_filter:
        filename += f"_{year_filter}"
    if month_filter:
        filename += f"_{month_filter:02d}"
    filename += ".pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )

# USER PROFILE ROUTES
@app.route('/profile')
@login_required
def user_profile():
    """View user profile"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get or create user profile
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Get user documents (excluding profile pictures since they don't require verification)
    documents = Document.query.filter_by(user_id=current_user.id, is_active=True).filter(Document.document_type != 'profile_picture').all()
    
    # Calculate profile completion percentage
    completion_percentage = calculate_profile_completion(current_user, profile)
    
    return render_template('user_profile.html', 
                         user=current_user, 
                         profile=profile, 
                         documents=documents,
                         completion_percentage=completion_percentage)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get or create user profile
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    form = UserProfileForm(obj=profile)
    # Pre-populate email field with current user's email
    if request.method == 'GET':
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        # Check if email is being changed and if new email already exists
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('This email address is already registered with another account.', 'error')
                return render_template('edit_profile.html', form=form, profile=profile)
        
        # Update basic user info including email
        current_user.email = form.email.data
        current_user.phone = form.alternate_phone.data or current_user.phone
        current_user.emergency_contact_name = form.emergency_contact_name.data
        current_user.emergency_contact_phone = form.emergency_contact_phone.data
        current_user.occupation = form.occupation.data
        current_user.aadhar_number = form.aadhar_number.data
        current_user.pan_number = form.pan_number.data
        
        # Update profile
        form.populate_obj(profile)
        profile.last_updated = datetime.utcnow()
        
        # Calculate and update profile completion
        completion_percentage = calculate_profile_completion(current_user, profile)
        current_user.profile_completion = completion_percentage
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))
    
    return render_template('edit_profile.html', form=form, profile=profile)

@app.route('/profile/upload_picture', methods=['GET', 'POST'])
@login_required
def upload_profile_picture():
    """Upload profile picture"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = ProfilePictureForm()
    
    if form.validate_on_submit():
        file = form.profile_picture.data
        if file:
            # Create uploads directory if it doesn't exist
            from werkzeug.utils import secure_filename
            
            uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"profile_{current_user.id}_{timestamp}_{file.filename}")
            file_path = os.path.join(uploads_dir, filename)
            
            # Save file
            file.save(file_path)
            
            # Update user profile picture
            current_user.profile_picture = f'uploads/profiles/{filename}'
            
            # No need to create a Document record for profile pictures as they don't require verification
            # Profile pictures are automatically approved when uploaded
            
            db.session.commit()
            flash('Profile picture uploaded successfully!', 'success')
            return redirect(url_for('user_profile'))
    
    return render_template('upload_profile_picture.html', form=form)

@app.route('/documents')
@login_required
def user_documents():
    """View user documents"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Exclude profile pictures since they don't require verification
    documents = Document.query.filter_by(user_id=current_user.id, is_active=True).filter(Document.document_type != 'profile_picture').order_by(Document.uploaded_at.desc()).all()
    
    # Group documents by type
    documents_by_type = {}
    for doc in documents:
        if doc.document_type not in documents_by_type:
            documents_by_type[doc.document_type] = []
        documents_by_type[doc.document_type].append(doc)
    
    return render_template('user_documents.html', 
                         documents=documents, 
                         documents_by_type=documents_by_type)

@app.route('/documents/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Upload a document"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        document_type = form.document_type.data
        description = form.description.data
        
        if file:
            from werkzeug.utils import secure_filename
            
            # Create uploads directory
            uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'documents')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{document_type}_{current_user.id}_{timestamp}_{file.filename}")
            file_path = os.path.join(uploads_dir, filename)
            
            # Check file size (10MB max)
            if file.content_length and file.content_length > 10 * 1024 * 1024:
                flash('File size too large. Maximum 10MB allowed.', 'error')
                return redirect(request.url)
            
            # Save file
            file.save(file_path)
            
            # Deactivate old documents of same type (keep history)
            old_docs = Document.query.filter_by(
                user_id=current_user.id, 
                document_type=document_type, 
                is_active=True
            ).all()
            for old_doc in old_docs:
                old_doc.is_active = False
            
            # Create new document record
            document = Document(
                user_id=current_user.id,
                document_type=document_type,
                filename=filename,
                original_filename=file.filename,
                file_path=f'uploads/documents/{filename}',
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type,
                admin_notes=description
            )
            db.session.add(document)
            
            # Create notification for admin
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                notification = Notification(
                    renter_id=current_user.id,
                    message=f'Document Uploaded: {current_user.username} uploaded a new {document_type.replace("_", " ").title()} document for verification.',
                    notification_type='document_upload'
                )
                db.session.add(notification)
            
            db.session.commit()
            flash(f'{document_type.replace("_", " ").title()} uploaded successfully! It will be verified by admin.', 'success')
            return redirect(url_for('user_documents'))
    
    return render_template('upload_document.html', form=form)

@app.route('/documents/view/<int:document_id>')
@login_required
def view_document(document_id):
    """View a document"""
    document = Document.query.get_or_404(document_id)
    
    # Check access permissions
    if not current_user.is_admin and document.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user_documents'))
    
    # Serve file
    file_path = os.path.join(app.root_path, 'static', document.file_path)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=False)
    else:
        flash('File not found.', 'error')
        return redirect(url_for('user_documents'))

@app.route('/documents/download/<int:document_id>')
@login_required
def download_document(document_id):
    """Download a document"""
    document = Document.query.get_or_404(document_id)
    
    # Check access permissions
    if not current_user.is_admin and document.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user_documents'))
    
    # Serve file for download
    file_path = os.path.join(app.root_path, 'static', document.file_path)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=document.original_filename)
    else:
        flash('File not found.', 'error')
        return redirect(url_for('user_documents'))

# Helper function to calculate profile completion
def calculate_profile_completion(user, profile):
    """Calculate profile completion percentage"""
    total_fields = 25  # Total number of profile fields
    completed_fields = 0
    
    # Basic user fields
    if user.phone: completed_fields += 1
    if user.emergency_contact_name: completed_fields += 1
    if user.emergency_contact_phone: completed_fields += 1
    if user.occupation: completed_fields += 1
    if user.aadhar_number: completed_fields += 1
    if user.pan_number: completed_fields += 1
    if user.profile_picture: completed_fields += 1
    
    # Profile fields
    if profile.full_name: completed_fields += 1
    if profile.date_of_birth: completed_fields += 1
    if profile.gender: completed_fields += 1
    if profile.nationality: completed_fields += 1
    if profile.marital_status: completed_fields += 1
    if profile.permanent_address: completed_fields += 1
    if profile.current_address: completed_fields += 1
    if profile.city: completed_fields += 1
    if profile.state: completed_fields += 1
    if profile.postal_code: completed_fields += 1
    if profile.country: completed_fields += 1
    if profile.alternate_phone: completed_fields += 1
    if profile.emergency_contact_relationship: completed_fields += 1
    if profile.company_name: completed_fields += 1
    if profile.job_title: completed_fields += 1
    if profile.monthly_income: completed_fields += 1
    if profile.lease_start_date: completed_fields += 1
    if profile.security_deposit: completed_fields += 1
    
    return int((completed_fields / total_fields) * 100)

# ADMIN ROUTES
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get all renters
    renters = User.query.filter_by(is_admin=False).all()
    
    # Get current month stats
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Calculate stats
    total_rent_collection = db.session.query(db.func.sum(RentPayment.amount)).filter(
        RentPayment.is_paid == True,
        RentPayment.month == current_month,
        RentPayment.year == current_year
    ).scalar() or 0
    
    total_electricity_collection = db.session.query(db.func.sum(ElectricityBill.total_amount)).filter(
        ElectricityBill.is_paid == True,
        ElectricityBill.month == current_month,
        ElectricityBill.year == current_year
    ).scalar() or 0
    
    pending_rent_payments = RentPayment.query.filter_by(
        is_paid=False,
        month=current_month,
        year=current_year
    ).count()
    
    pending_electricity_bills = ElectricityBill.query.filter_by(
        is_paid=False,
        month=current_month,
        year=current_year
    ).count()
    
    # Get pending payment verifications count
    pending_rent_verifications = RentPayment.query.filter_by(payment_status='pending').count()
    pending_electricity_verifications = ElectricityBill.query.filter_by(payment_status='pending').count()
    
    # Get pending document verifications count
    pending_document_verifications = Document.query.filter_by(
        verification_status='pending',
        is_active=True
    ).count()
    
    return render_template('admin_dashboard.html',
                         renters=renters,
                         total_rent_collection=total_rent_collection,
                         total_electricity_collection=total_electricity_collection,
                         pending_rent_payments=pending_rent_payments,
                         pending_electricity_bills=pending_electricity_bills,
                         pending_rent_verifications=pending_rent_verifications,
                         pending_electricity_verifications=pending_electricity_verifications,
                         pending_document_verifications=pending_document_verifications,
                         current_month=current_month)

@app.route('/admin/profiles')
@login_required
def admin_profiles():
    """View all user profiles for admin"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get all non-admin users with their profiles
    users = User.query.filter_by(is_admin=False).all()
    
    user_profiles = []
    for user in users:
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
        
        completion_percentage = calculate_profile_completion(user, profile)
        
        user_profiles.append({
            'user': user,
            'profile': profile,
            'completion_percentage': completion_percentage
        })
    
    # Sort by completion percentage (lowest first to highlight incomplete profiles)
    user_profiles.sort(key=lambda x: x['completion_percentage'])
    
    return render_template('admin_profiles.html', user_profiles=user_profiles)

@app.route('/admin/documents')
@login_required
def admin_documents():
    """View and manage all user documents"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get verification status filter
    status_filter = request.args.get('status', 'all')
    user_filter = request.args.get('user_id', type=int)
    
    # Base query - exclude profile pictures
    query = Document.query.filter(Document.document_type != 'profile_picture', Document.is_active == True)
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter(Document.verification_status == status_filter)
    
    if user_filter:
        query = query.filter(Document.user_id == user_filter)
    
    # Get documents with user info
    documents = query.join(User, Document.user_id == User.id).order_by(Document.uploaded_at.desc()).all()
    
    # Get all users for filter dropdown
    users = User.query.filter_by(is_admin=False).order_by(User.username).all()
    
    # Count documents by status
    pending_count = Document.query.filter_by(verification_status='pending', is_active=True).filter(Document.document_type != 'profile_picture').count()
    approved_count = Document.query.filter_by(verification_status='approved', is_active=True).filter(Document.document_type != 'profile_picture').count()
    rejected_count = Document.query.filter_by(verification_status='rejected', is_active=True).filter(Document.document_type != 'profile_picture').count()
    
    return render_template('admin_documents.html', 
                         documents=documents, 
                         users=users,
                         status_filter=status_filter,
                         user_filter=user_filter,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         rejected_count=rejected_count)

@app.route('/admin/document/verify/<int:document_id>', methods=['GET', 'POST'])
@login_required
def verify_document(document_id):
    """Verify/reject a document"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    document = Document.query.get_or_404(document_id)
    form = DocumentVerificationForm()
    
    if form.validate_on_submit():
        document.verification_status = form.status.data
        document.admin_notes = form.admin_notes.data
        document.verified_by = current_user.id
        document.verified_at = datetime.utcnow()
        
        # Create notification for user
        notification_message = f"Document Verification: Your {document.document_type.replace('_', ' ').title()} document has been {form.status.data}."
        if form.admin_notes.data:
            notification_message += f" Note: {form.admin_notes.data}"
            
        notification = Notification(
            renter_id=document.user_id,
            message=notification_message,
            notification_type='document_verification'
        )
        db.session.add(notification)
        
        db.session.commit()
        flash(f'Document {form.status.data} successfully!', 'success')
        return redirect(url_for('admin_documents'))
    
    return render_template('verify_document.html', document=document, form=form)

@app.route('/admin/reading_history')
@login_required
def admin_reading_history():
    """View all meter readings across all renters"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get filter parameters
    renter_filter = request.args.get('renter_id', type=int)
    year_filter = request.args.get('year', type=int)
    month_filter = request.args.get('month', type=int)
    
    # Base query
    query = MeterReading.query.join(User, MeterReading.renter_id == User.id)
    
    # Apply filters
    if renter_filter:
        query = query.filter(MeterReading.renter_id == renter_filter)
    if year_filter:
        query = query.filter(MeterReading.year == year_filter)
    if month_filter:
        query = query.filter(MeterReading.month == month_filter)
    
    # Get readings ordered by date (most recent first)
    readings = query.order_by(MeterReading.year.desc(), MeterReading.month.desc()).all()
    
    # Get all active renters for filter dropdown
    renters = User.query.filter_by(is_admin=False, is_active=True).order_by(User.username).all()
    
    # Get unique years for filter
    years = sorted(set([r.year for r in MeterReading.query.all()]), reverse=True)
    
    # Calculate statistics
    total_readings = len(readings)
    total_units = sum([r.units_consumed for r in readings])
    
    return render_template('admin_reading_history.html', 
                         readings=readings,
                         renters=renters,
                         years=years,
                         renter_filter=renter_filter,
                         year_filter=year_filter,
                         month_filter=month_filter,
                         total_readings=total_readings,
                         total_units=total_units)

@app.route('/admin/view_profile/<int:user_id>')
@login_required
def admin_view_profile(user_id):
    """View detailed profile of a specific user"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot view admin profiles.', 'error')
        return redirect(url_for('admin_profiles'))
    
    # Get or create user profile
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
    
    # Calculate profile completion
    completion_percentage = calculate_profile_completion(user, profile)
    
    # Get user documents
    documents = Document.query.filter_by(user_id=user.id, is_active=True)\
        .order_by(Document.uploaded_at.desc()).all()
    
    # Group documents by type
    documents_by_type = {}
    for doc in documents:
        documents_by_type.setdefault(doc.document_type, []).append(doc)
    
    # Get payment history
    rent_payments = RentPayment.query.filter_by(renter_id=user.id)\
        .order_by(RentPayment.year.desc(), RentPayment.month.desc()).limit(12).all()
    electricity_bills = ElectricityBill.query.filter_by(renter_id=user.id)\
        .order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).limit(12).all()
    meter_readings = MeterReading.query.filter_by(renter_id=user.id)\
        .order_by(MeterReading.year.desc(), MeterReading.month.desc()).limit(12).all()
    
    return render_template('admin_view_profile.html',
                         user=user,
                         profile=profile,
                         completion_percentage=completion_percentage,
                         documents=documents,
                         documents_by_type=documents_by_type,
                         rent_payments=rent_payments,
                         electricity_bills=electricity_bills,
                         meter_readings=meter_readings)

@app.route('/admin/bills')
@login_required
def admin_bills():
    """View all electricity bills"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get filter parameters
    renter_filter = request.args.get('renter_id', type=int)
    year_filter = request.args.get('year', type=int)
    month_filter = request.args.get('month', type=int)
    status_filter = request.args.get('status', '')
    
    # Base query
    query = ElectricityBill.query.join(User, ElectricityBill.renter_id == User.id)
    
    # Apply filters
    if renter_filter:
        query = query.filter(ElectricityBill.renter_id == renter_filter)
    if year_filter:
        query = query.filter(ElectricityBill.year == year_filter)
    if month_filter:
        query = query.filter(ElectricityBill.month == month_filter)
    if status_filter:
        if status_filter == 'paid':
            query = query.filter(ElectricityBill.is_paid == True)
        elif status_filter == 'unpaid':
            query = query.filter(ElectricityBill.is_paid == False)
        elif status_filter == 'pending':
            query = query.filter(ElectricityBill.payment_status == 'pending')
    
    # Get bills ordered by date (most recent first)
    bills = query.order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
    
    # Get all active renters for filter dropdown
    renters = User.query.filter_by(is_admin=False, is_active=True).order_by(User.username).all()
    
    # Get unique years for filter
    years = sorted(set([b.year for b in ElectricityBill.query.all()]), reverse=True)
    
    # Calculate statistics
    total_bills = len(bills)
    total_amount = sum([b.total_amount for b in bills])
    paid_amount = sum([b.amount_paid or 0 for b in bills])
    outstanding_amount = total_amount - paid_amount
    
    return render_template('admin_bills.html',
                         bills=bills,
                         renters=renters,
                         years=years,
                         renter_filter=renter_filter,
                         year_filter=year_filter,
                         month_filter=month_filter,
                         status_filter=status_filter,
                         total_bills=total_bills,
                         total_amount=total_amount,
                         paid_amount=paid_amount,
                         outstanding_amount=outstanding_amount)

@app.route('/admin/monthly_report')
@login_required
def admin_monthly_report():
    """Generate monthly collection report"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get filter parameters
    year_filter = request.args.get('year', type=int) or datetime.now().year
    month_filter = request.args.get('month', type=int) or datetime.now().month
    
    # Get rent payments for the month
    rent_payments = RentPayment.query.filter_by(year=year_filter, month=month_filter).all()
    
    # Get electricity bills for the month
    electricity_bills = ElectricityBill.query.filter_by(year=year_filter, month=month_filter).all()
    
    # Calculate totals
    rent_total = sum([p.amount for p in rent_payments])
    rent_collected = sum([p.amount for p in rent_payments if p.is_paid])
    rent_pending = rent_total - rent_collected
    
    electricity_total = sum([b.total_amount for b in electricity_bills])
    electricity_collected = sum([b.amount_paid or 0 for b in electricity_bills])
    electricity_pending = electricity_total - electricity_collected
    
    # Get unique years for filter
    years = sorted(set([p.year for p in RentPayment.query.all()]), reverse=True)
    
    report_data = {
        'year': year_filter,
        'month': month_filter,
        'month_name': calendar.month_name[month_filter],
        'rent_total': rent_total,
        'rent_collected': rent_collected,
        'rent_pending': rent_pending,
        'electricity_total': electricity_total,
        'electricity_collected': electricity_collected,
        'electricity_pending': electricity_pending,
        'total_collected': rent_collected + electricity_collected,
        'total_pending': rent_pending + electricity_pending,
        'rent_payments': rent_payments,
        'electricity_bills': electricity_bills
    }
    
    return render_template('admin_monthly_report.html',
                         report=report_data,
                         years=years,
                         year_filter=year_filter,
                         month_filter=month_filter)

@app.route('/admin/pending_payments')
@login_required
def admin_pending_payments():
    """View all pending payment verifications"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get pending rent payments
    pending_rent = RentPayment.query.filter_by(payment_status='pending')\
        .join(User, RentPayment.renter_id == User.id).order_by(RentPayment.payment_date.desc()).all()
    
    # Get pending electricity payments
    pending_electricity = ElectricityBill.query.filter_by(payment_status='pending')\
        .join(User, ElectricityBill.renter_id == User.id).order_by(ElectricityBill.payment_date.desc()).all()
    
    return render_template('admin_pending_payments.html',
                         pending_rent=pending_rent,
                         pending_electricity=pending_electricity)

@app.route('/admin/verify_payment/<payment_type>/<int:payment_id>', methods=['POST'])
@login_required
def verify_payment(payment_type, payment_id):
    """Verify or reject a payment"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    action = request.form.get('action')  # 'approve' or 'reject'
    admin_notes = request.form.get('admin_notes', '').strip()
    
    if payment_type == 'rent':
        payment = RentPayment.query.get_or_404(payment_id)
        if action == 'approve':
            payment.is_paid = True
            payment.payment_status = 'approved'
        else:
            payment.payment_status = 'rejected'
    elif payment_type == 'electricity':
        payment = ElectricityBill.query.get_or_404(payment_id)
        if action == 'approve':
            payment.is_paid = True
            payment.payment_status = 'approved'
            payment.amount_paid = payment.total_amount
        else:
            payment.payment_status = 'rejected'
    
    # Add admin notes
    if admin_notes:
        payment.verification_notes = admin_notes
    
    payment.verification_date = datetime.now()
    payment.verified_by = current_user.id
    
    # Create notification for user
    notification_message = f"Payment {action.title()}: Your {payment_type} payment has been {action}ed."
    if admin_notes:
        notification_message += f" Note: {admin_notes}"
    
    notification = Notification(
        renter_id=payment.renter_id,
        message=notification_message,
        notification_type='payment_verification'
    )
    db.session.add(notification)
    
    db.session.commit()
    flash(f'Payment {action}ed successfully!', 'success')
    return redirect(url_for('admin_pending_payments'))

@app.route('/admin/edit_rent_payment/<int:payment_id>', methods=['GET', 'POST'])
@login_required
def edit_rent_payment(payment_id):
    """Edit rent payment details"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    payment = RentPayment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        # Update payment details
        payment.amount = float(request.form.get('amount', payment.amount))
        payment.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        
        # Handle payment status
        if request.form.get('is_paid') == 'on':
            payment.is_paid = True
            payment.payment_status = 'approved'
            if not payment.payment_date:
                payment.payment_date = datetime.now()
        else:
            payment.is_paid = False
            payment.payment_status = request.form.get('payment_status', 'pending')
        
        # Update admin notes
        admin_notes = request.form.get('admin_notes', '').strip()
        if admin_notes:
            payment.verification_notes = admin_notes
        
        db.session.commit()
        flash('Rent payment updated successfully!', 'success')
        return redirect(url_for('view_renter', renter_id=payment.renter_id))
    
    return render_template('edit_rent_payment.html', payment=payment)

@app.route('/admin/edit_electricity_bill/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_electricity_bill(bill_id):
    """Edit electricity bill details"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    
    if request.method == 'POST':
        # Update bill details
        bill.rate_per_unit = float(request.form.get('rate_per_unit', bill.rate_per_unit))
        bill.fixed_charge = float(request.form.get('fixed_charge', bill.fixed_charge))
        bill.units_consumed = float(request.form.get('units_consumed', bill.units_consumed))
        
        # Recalculate total amount
        bill.total_amount = (bill.units_consumed * bill.rate_per_unit) + bill.fixed_charge
        
        # Handle payment status
        if request.form.get('is_paid') == 'on':
            bill.is_paid = True
            bill.payment_status = 'approved'
            bill.amount_paid = bill.total_amount
            if not bill.payment_date:
                bill.payment_date = datetime.now()
        else:
            bill.is_paid = False
            bill.payment_status = request.form.get('payment_status', 'pending')
            bill.amount_paid = float(request.form.get('amount_paid', bill.amount_paid or 0))
        
        # Update units paid
        bill.units_paid = float(request.form.get('units_paid', bill.units_paid or 0))
        
        # Update admin notes
        admin_notes = request.form.get('admin_notes', '').strip()
        if admin_notes:
            bill.verification_notes = admin_notes
        
        db.session.commit()
        flash('Electricity bill updated successfully!', 'success')
        return redirect(url_for('view_renter', renter_id=bill.renter_id))
    
    return render_template('edit_electricity_bill.html', bill=bill)

@app.route('/admin/user_payment_history')
@login_required
def admin_user_payment_history():
    """Simple view showing userwise payment history - when they paid rent and how many units paid"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get all non-admin users
    users = User.query.filter_by(is_admin=False, is_approved=True).order_by(User.username).all()
    
    user_payment_data = []
    
    for user in users:
        # Get all rent payments that are paid
        rent_payments = RentPayment.query.filter_by(
            renter_id=user.id, 
            is_paid=True
        ).order_by(RentPayment.year.desc(), RentPayment.month.desc()).all()
        
        # Get all electricity bills that are paid
        electricity_bills = ElectricityBill.query.filter_by(
            renter_id=user.id, 
            is_paid=True
        ).order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
        
        # Combine payment data by date for table format
        payment_records = []
        
        # Add rent payment records
        for rent in rent_payments:
            try:
                amount = float(rent.amount) if rent.amount is not None else 0.0
            except (ValueError, TypeError):
                amount = 0.0
                
            payment_records.append({
                'date': rent.payment_date.strftime('%Y-%m-%d') if rent.payment_date else f"{rent.year}-{rent.month:02d}-01",
                'month_year': f"{calendar.month_name[rent.month]} {rent.year}",
                'type': 'rent',
                'amount': amount,
                'units_paid': 0.0,  # Rent doesn't have units
                'payment_date': rent.payment_date
            })
        
        # Add electricity payment records
        for bill in electricity_bills:
            try:
                amount = bill.amount_paid or bill.total_amount
                amount = float(amount) if amount is not None else 0.0
            except (ValueError, TypeError):
                amount = 0.0
                
            try:
                units = bill.units_paid or bill.units_consumed
                units = float(units) if units is not None else 0.0
            except (ValueError, TypeError):
                units = 0.0
                
            payment_records.append({
                'date': bill.payment_date.strftime('%Y-%m-%d') if bill.payment_date else f"{bill.year}-{bill.month:02d}-01",
                'month_year': f"{calendar.month_name[bill.month]} {bill.year}",
                'type': 'electricity',
                'amount': amount,
                'units_paid': units,
                'payment_date': bill.payment_date
            })
        
        # Sort by payment date (most recent first)
        payment_records.sort(key=lambda x: x['payment_date'] or datetime.min, reverse=True)
        
        # Calculate totals
        total_rent_payments = len([p for p in payment_records if p['type'] == 'rent'])
        total_electricity_payments = len([p for p in payment_records if p['type'] == 'electricity'])
        
        # Calculate total units paid with error handling
        total_units_paid = 0.0
        for p in payment_records:
            if p['type'] == 'electricity':
                try:
                    units = float(p['units_paid']) if p['units_paid'] is not None else 0.0
                    total_units_paid += units
                except (ValueError, TypeError):
                    continue
        
        user_payment_data.append({
            'user': user,
            'payment_records': payment_records,
            'total_rent_payments': total_rent_payments,
            'total_electricity_payments': total_electricity_payments,
            'total_units_paid': total_units_paid
        })
    
    return render_template('admin_user_payment_history.html', user_payment_data=user_payment_data)

@app.route('/admin/renters')
@login_required
def admin_renters():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    active_renters = User.query.filter_by(is_admin=False, is_active=True, is_approved=True).all()
    inactive_renters = User.query.filter_by(is_admin=False, is_active=False).all()
    pending_renters = User.query.filter_by(is_admin=False, is_approved=False).all()
    
    return render_template('admin_renters.html', 
                         active_renters=active_renters,
                         inactive_renters=inactive_renters,
                         pending_renters=pending_renters)

@app.route('/admin/add_meter_reading', methods=['GET', 'POST'])
@login_required
def add_meter_reading():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    form = MeterReadingForm()
    
    # Populate renter choices
    renters = User.query.filter_by(is_admin=False, is_active=True).all()
    form.renter_id.choices = [(r.id, f"{r.username} - Room {r.room_number}") for r in renters]
    
    if form.validate_on_submit():
        renter = User.query.get(form.renter_id.data)
        
        # Get previous reading
        previous_reading = MeterReading.query.filter_by(
            renter_id=renter.id
        ).order_by(MeterReading.year.desc(), MeterReading.month.desc()).first()
        
        previous_value = previous_reading.current_reading if previous_reading else 0
        
        # Calculate units consumed
        units_consumed = form.current_reading.data - previous_value
        
        if units_consumed < 0:
            flash('Current reading cannot be less than previous reading.', 'error')
            return render_template('add_meter_reading.html', form=form)
        
        # Create meter reading
        meter_reading = MeterReading(
            renter_id=renter.id,
            current_reading=form.current_reading.data,
            previous_reading=previous_value,
            units_consumed=units_consumed,
            month=form.month.data,
            year=form.year.data
        )
        db.session.add(meter_reading)
        db.session.flush()  # Get the ID
        
        # Create electricity bill
        electricity_bill = calculate_electricity_bill(meter_reading)
        db.session.add(electricity_bill)
        
        # Create monthly rent payment if doesn't exist
        create_monthly_rent_payment(renter, form.month.data, form.year.data)
        
        db.session.commit()
        flash('Meter reading added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_meter_reading.html', form=form)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    settings = SystemSettings.query.first()
    if not settings:
        settings = SystemSettings()
        db.session.add(settings)
        db.session.commit()
    
    form = SystemSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        settings.electricity_rate = form.electricity_rate.data
        settings.fixed_charge = form.fixed_charge.data
        settings.rent_due_date = form.rent_due_date.data
        settings.updated_at = datetime.now()
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin_settings.html', form=form, settings=settings)

@app.route('/admin/approve_renter/<int:renter_id>')
@login_required
def approve_renter(renter_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    renter = User.query.get_or_404(renter_id)
    renter.is_approved = True
    db.session.commit()
    
    flash(f'Renter {renter.username} has been approved successfully!', 'success')
    return redirect(url_for('admin_renters'))

@app.route('/admin/reject_renter/<int:renter_id>')
@login_required
def reject_renter(renter_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    renter = User.query.get_or_404(renter_id)
    db.session.delete(renter)
    db.session.commit()
    
    flash(f'Renter {renter.username} has been rejected and removed.', 'info')
    return redirect(url_for('admin_renters'))

@app.route('/admin/edit_renter/<int:renter_id>', methods=['GET', 'POST'])
@login_required
def edit_renter(renter_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    renter = User.query.get_or_404(renter_id)
    form = EditRenterForm(obj=renter)
    
    if form.validate_on_submit():
        # Check if email is being changed and if new email already exists
        if form.email.data != renter.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('This email address is already registered with another user.', 'error')
                return render_template('edit_renter.html', form=form, renter=renter)
        
        # Check if username is being changed and if new username already exists
        if form.username.data != renter.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('This username is already taken by another user.', 'error')
                return render_template('edit_renter.html', form=form, renter=renter)
        
        renter.username = form.username.data
        renter.email = form.email.data
        renter.phone = form.phone.data
        renter.room_number = form.room_number.data
        renter.rent_amount = form.rent_amount.data
        renter.is_active = form.is_active.data
        renter.is_approved = form.is_approved.data
        db.session.commit()
        flash('Renter updated successfully!', 'success')
        return redirect(url_for('admin_renters'))
    
    return render_template('edit_renter.html', form=form, renter=renter)

@app.route('/admin/view_renter/<int:renter_id>')
@login_required
def view_renter(renter_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    renter = User.query.get_or_404(renter_id)
    
    # Get payment history
    rent_payments = RentPayment.query.filter_by(renter_id=renter.id).order_by(RentPayment.year.desc(), RentPayment.month.desc()).all()
    electricity_bills = ElectricityBill.query.filter_by(renter_id=renter.id).order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
    meter_readings = MeterReading.query.filter_by(renter_id=renter.id).order_by(MeterReading.year.desc(), MeterReading.month.desc()).all()
    
    # Get documents for verification
    documents = Document.query.filter_by(user_id=renter.id, is_active=True).order_by(Document.uploaded_at.desc()).all()
    
    # Group documents by type
    documents_by_type = {}
    for doc in documents:
        documents_by_type.setdefault(doc.document_type, []).append(doc)
    
    return render_template('view_renter.html',
                         renter=renter,
                         rent_payments=rent_payments,
                         electricity_bills=electricity_bills,
                         meter_readings=meter_readings,
                         documents=documents,
                         documents_by_type=documents_by_type)

@app.route('/admin/payment_history')
@login_required
def admin_payment_history():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get all renters
    renters = User.query.filter_by(is_admin=False, is_approved=True).all()
    
    payment_history_by_renter = {}
    
    for renter in renters:
        # Get rent payments
        rent_payments = RentPayment.query.filter_by(renter_id=renter.id)\
            .order_by(RentPayment.year.desc(), RentPayment.month.desc()).all()
        
        # Get electricity bills with meter readings
        electricity_bills = ElectricityBill.query.filter_by(renter_id=renter.id)\
            .join(MeterReading, ElectricityBill.meter_reading_id == MeterReading.id).order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
        
        # Combine and organize by month/year
        combined_history = {}
        
        # Add rent payments
        for rent in rent_payments:
            month_key = f"{rent.year}-{rent.month:02d}"
            if month_key not in combined_history:
                combined_history[month_key] = {
                    'year': rent.year,
                    'month': rent.month,
                    'month_name': calendar.month_name[rent.month],
                    'rent_payment': None,
                    'electricity_bill': None,
                    'meter_reading': None
                }
            combined_history[month_key]['rent_payment'] = rent
        
        # Add electricity bills
        for bill in electricity_bills:
            month_key = f"{bill.year}-{bill.month:02d}"
            if month_key not in combined_history:
                combined_history[month_key] = {
                    'year': bill.year,
                    'month': bill.month,
                    'month_name': calendar.month_name[bill.month],
                    'rent_payment': None,
                    'electricity_bill': None,
                    'meter_reading': None
                }
            combined_history[month_key]['electricity_bill'] = bill
            combined_history[month_key]['meter_reading'] = bill.meter_reading
        
        # Sort by year and month (most recent first)
        sorted_history = sorted(combined_history.values(), 
                              key=lambda x: (x['year'], x['month']), reverse=True)
        
        # Calculate totals
        total_rent_due = sum([h['rent_payment'].amount for h in sorted_history if h['rent_payment']], start=Decimal('0'))
        total_rent_paid = sum([h['rent_payment'].amount for h in sorted_history if h['rent_payment'] and h['rent_payment'].is_paid], start=Decimal('0'))
        total_electricity_due = sum([h['electricity_bill'].total_amount for h in sorted_history if h['electricity_bill']], start=Decimal('0'))
        total_electricity_paid = sum([h['electricity_bill'].amount_paid or 0 for h in sorted_history if h['electricity_bill']], start=Decimal('0'))
        total_units_consumed = sum([h['meter_reading'].units_consumed for h in sorted_history if h['meter_reading']], start=Decimal('0'))
        total_units_paid = sum([h['electricity_bill'].units_paid or 0 for h in sorted_history if h['electricity_bill']], start=Decimal('0'))
        
        payment_history_by_renter[renter.id] = {
            'renter': renter,
            'history': sorted_history,
            'totals': {
                'rent_due': total_rent_due,
                'rent_paid': total_rent_paid,
                'electricity_due': total_electricity_due,
                'electricity_paid': total_electricity_paid,
                'units_consumed': total_units_consumed,
                'units_paid': total_units_paid,
                'rent_outstanding': total_rent_due - total_rent_paid,
                'electricity_outstanding': total_electricity_due - total_electricity_paid,
                'units_outstanding': total_units_consumed - total_units_paid
            }
        }
    
    return render_template('admin_payment_history.html', payment_history_by_renter=payment_history_by_renter)

@app.route('/admin/payment_history_table')
@login_required
def admin_payment_history_table():
    """Admin view for payment history in tabular format like the handwritten table"""
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get filter parameters
    year_filter = request.args.get('year', type=int)
    month_filter = request.args.get('month', type=int)
    renter_filter = request.args.get('renter_id', type=int)
    format_type = request.args.get('format', '').lower()
    
    # Base query for both rent and electricity payments
    rent_query = RentPayment.query.join(User, RentPayment.renter_id == User.id).filter(RentPayment.is_paid == True)
    electricity_query = ElectricityBill.query.join(User, ElectricityBill.renter_id == User.id).filter(ElectricityBill.is_paid == True)
    
    # Apply filters
    if year_filter:
        rent_query = rent_query.filter(RentPayment.year == year_filter)
        electricity_query = electricity_query.filter(ElectricityBill.year == year_filter)
    
    if month_filter:
        rent_query = rent_query.filter(RentPayment.month == month_filter)
        electricity_query = electricity_query.filter(ElectricityBill.month == month_filter)
        
    if renter_filter:
        rent_query = rent_query.filter(RentPayment.renter_id == renter_filter)
        electricity_query = electricity_query.filter(ElectricityBill.renter_id == renter_filter)
    
    # Get the data
    rent_payments = rent_query.order_by(RentPayment.payment_date.desc()).all()
    electricity_bills = electricity_query.order_by(ElectricityBill.payment_date.desc()).all()
    
    # Combine payments by date and user for table format
    payment_records = []
    
    # Process rent payments
    for rent in rent_payments:
        # Find corresponding electricity bill for same month/year/user
        electricity_bill = None
        for bill in electricity_bills:
            if (bill.renter_id == rent.renter_id and 
                bill.month == rent.month and 
                bill.year == rent.year):
                electricity_bill = bill
                break
        
        # Create combined record
        total_received = float(rent.amount or 0)
        electric_amount = 0
        units_consumed = 0
        
        if electricity_bill:
            electric_amount = float(electricity_bill.amount_paid or electricity_bill.total_amount or 0)
            units_consumed = float(electricity_bill.units_consumed or 0)
            total_received += electric_amount
        
        payment_records.append({
            'date': rent.payment_date.strftime('%d-%m-%Y') if rent.payment_date else f"{rent.month:02d}-{rent.year}",
            'renter': rent.renter,
            'total_received': total_received,
            'flat_rent': float(rent.amount or 0),
            'electric_bill': electric_amount,
            'units_consumed': units_consumed,
            'month': f"{calendar.month_name[rent.month]} {rent.year}",
            'payment_method': rent.payment_method or 'Cash',
            'payment_date': rent.payment_date,
            'rent_id': rent.id,
            'electricity_id': electricity_bill.id if electricity_bill else None
        })
    
    # Add electricity bills that don't have corresponding rent payments
    for bill in electricity_bills:
        # Check if this bill is already included in rent payments
        already_included = False
        for record in payment_records:
            if (record['renter'].id == bill.renter_id and 
                record['electricity_id'] == bill.id):
                already_included = True
                break
        
        if not already_included:
            electric_amount = float(bill.amount_paid or bill.total_amount or 0)
            payment_records.append({
                'date': bill.payment_date.strftime('%d-%m-%Y') if bill.payment_date else f"{bill.month:02d}-{bill.year}",
                'renter': bill.renter,
                'total_received': electric_amount,
                'flat_rent': 0,
                'electric_bill': electric_amount,
                'units_consumed': float(bill.units_consumed or 0),
                'month': f"{calendar.month_name[bill.month]} {bill.year}",
                'payment_method': bill.payment_method or 'Cash',
                'payment_date': bill.payment_date,
                'rent_id': None,
                'electricity_id': bill.id
            })
    
    # Sort by payment date (most recent first)
    payment_records.sort(key=lambda x: x['payment_date'] or datetime.min, reverse=True)
    
    # Calculate totals
    total_amount = sum([record['total_received'] for record in payment_records])
    total_rent = sum([record['flat_rent'] for record in payment_records])
    total_electricity = sum([record['electric_bill'] for record in payment_records])
    total_units = sum([record['units_consumed'] for record in payment_records])
    
    # Get filter options
    renters = User.query.filter_by(is_admin=False, is_active=True).order_by(User.username).all()
    years = sorted(set([r.year for r in RentPayment.query.all()] + [b.year for b in ElectricityBill.query.all()]), reverse=True)
    
    # Handle export requests
    if format_type == 'excel':
        return export_payment_table_excel(payment_records, year_filter, month_filter, renter_filter)
    elif format_type == 'pdf':
        return export_payment_table_pdf(payment_records, year_filter, month_filter, renter_filter)
    
    return render_template('admin_payment_history_table.html',
                         payment_records=payment_records,
                         total_amount=total_amount,
                         total_rent=total_rent,
                         total_electricity=total_electricity,
                         total_units=total_units,
                         renters=renters,
                         years=years,
                         year_filter=year_filter,
                         month_filter=month_filter,
                         renter_filter=renter_filter)

def export_payment_table_excel(payment_records, year_filter, month_filter, renter_filter):
    """Export payment history table to Excel"""
    # Create DataFrame
    data = []
    for record in payment_records:
        data.append({
            'Date': record['date'],
            'Renter': record['renter'].username,
            'Room': record['renter'].room_number,
            'Total Received': record['total_received'],
            'Flat Rent': record['flat_rent'],
            'Electric Bill': record['electric_bill'],
            'Units Consumed': record['units_consumed'],
            'Month': record['month'],
            'Payment Method': record['payment_method']
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Payment History', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Payment History']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_name = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_name].width = adjusted_width
    
    output.seek(0)
    
    # Generate filename
    filter_parts = []
    if year_filter:
        filter_parts.append(f"Year_{year_filter}")
    if month_filter:
        filter_parts.append(f"Month_{month_filter}")
    if renter_filter:
        renter = User.query.get(renter_filter)
        if renter:
            filter_parts.append(f"Renter_{renter.username}")
    
    filter_str = "_".join(filter_parts) if filter_parts else "All"
    filename = f"Payment_History_{filter_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_payment_table_pdf(payment_records, year_filter, month_filter, renter_filter):
    """Export payment history table to PDF"""
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = 1  # Center alignment
    
    filter_info = []
    if year_filter:
        filter_info.append(f"Year: {year_filter}")
    if month_filter:
        filter_info.append(f"Month: {calendar.month_name[month_filter]}")
    if renter_filter:
        renter = User.query.get(renter_filter)
        if renter:
            filter_info.append(f"Renter: {renter.username}")
    
    title_text = "Payment History Table"
    if filter_info:
        title_text += f" ({', '.join(filter_info)})"
    
    title = Paragraph(title_text, title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Create table data
    table_data = [['Date', 'Renter', 'Room', 'Total Received', 'Flat Rent', 'Electric Bill', 'Units', 'Month']]
    
    for record in payment_records:
        table_data.append([
            record['date'],
            record['renter'].username,
            str(record['renter'].room_number),
            f"₹{record['total_received']:.2f}",
            f"₹{record['flat_rent']:.2f}",
            f"₹{record['electric_bill']:.2f}",
            f"{record['units_consumed']:.1f}",
            record['month']
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Add summary
    elements.append(Spacer(1, 12))
    total_amount = sum([record['total_received'] for record in payment_records])
    total_rent = sum([record['flat_rent'] for record in payment_records])
    total_electricity = sum([record['electric_bill'] for record in payment_records])
    total_units = sum([record['units_consumed'] for record in payment_records])
    
    summary_style = styles['Normal']
    summary_style.alignment = 1
    summary_text = f"<b>Summary:</b> Total Amount: ₹{total_amount:.2f}, Total Rent: ₹{total_rent:.2f}, Total Electricity: ₹{total_electricity:.2f}, Total Units: {total_units:.1f}"
    summary = Paragraph(summary_text, summary_style)
    elements.append(summary)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Generate filename
    filter_parts = []
    if year_filter:
        filter_parts.append(f"Year_{year_filter}")
    if month_filter:
        filter_parts.append(f"Month_{month_filter}")
    if renter_filter:
        renter = User.query.get(renter_filter)
        if renter:
            filter_parts.append(f"Renter_{renter.username}")
    
    filter_str = "_".join(filter_parts) if filter_parts else "All"
    filename = f"Payment_History_{filter_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

def export_renter_payment_table_excel(payment_records, user, year_filter, month_filter):
    """Export renter payment history table to Excel"""
    # Create DataFrame
    data = []
    for record in payment_records:
        data.append({
            'Date': record['date'],
            'Total Received': record['total_received'],
            'Flat Rent': record['flat_rent'],
            'Electric Bill': record['electric_bill'],
            'Units Consumed': record['units_consumed'],
            'Month': record['month'],
            'Payment Method': record['payment_method']
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='My Payment History', index=False)
        
        # Auto-adjust column widths
        workbook = writer.book
        worksheet = writer.sheets['My Payment History']
        
        for column in worksheet.columns:
            max_length = 0
            column_name = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_name].width = adjusted_width
    
    output.seek(0)
    
    # Generate filename
    filter_parts = [f"User_{user.username}"]
    if year_filter:
        filter_parts.append(f"Year_{year_filter}")
    if month_filter:
        filter_parts.append(f"Month_{month_filter}")
    
    filter_str = "_".join(filter_parts)
    filename = f"My_Payment_History_{filter_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_renter_payment_table_pdf(payment_records, user, year_filter, month_filter):
    """Export renter payment history table to PDF"""
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = 1  # Center alignment
    
    filter_info = [f"User: {user.username} (Room {user.room_number})"]
    if year_filter:
        filter_info.append(f"Year: {year_filter}")
    if month_filter:
        filter_info.append(f"Month: {calendar.month_name[month_filter]}")
    
    title_text = f"My Payment History"
    if len(filter_info) > 1:
        title_text += f" ({', '.join(filter_info[1:])})"
    
    title = Paragraph(title_text, title_style)
    elements.append(title)
    elements.append(Spacer(1, 6))
    
    # User info
    user_info = Paragraph(f"<b>Renter:</b> {user.username} | <b>Room:</b> {user.room_number}", styles['Normal'])
    elements.append(user_info)
    elements.append(Spacer(1, 12))
    
    # Create table data
    table_data = [['Date', 'Total Received', 'Flat Rent', 'Electric Bill', 'Units', 'Month', 'Payment Method']]
    
    for record in payment_records:
        table_data.append([
            record['date'],
            f"₹{record['total_received']:.2f}",
            f"₹{record['flat_rent']:.2f}",
            f"₹{record['electric_bill']:.2f}",
            f"{record['units_consumed']:.1f}",
            record['month'],
            record['payment_method']
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    
    # Add summary
    elements.append(Spacer(1, 12))
    total_amount = sum([record['total_received'] for record in payment_records])
    total_rent = sum([record['flat_rent'] for record in payment_records])
    total_electricity = sum([record['electric_bill'] for record in payment_records])
    total_units = sum([record['units_consumed'] for record in payment_records])
    
    summary_style = styles['Normal']
    summary_style.alignment = 1
    summary_text = f"<b>Summary:</b> Total Amount: ₹{total_amount:.2f}, Total Rent: ₹{total_rent:.2f}, Total Electricity: ₹{total_electricity:.2f}, Total Units: {total_units:.1f}"
    summary = Paragraph(summary_text, summary_style)
    elements.append(summary)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Generate filename
    filter_parts = [f"User_{user.username}"]
    if year_filter:
        filter_parts.append(f"Year_{year_filter}")
    if month_filter:
        filter_parts.append(f"Month_{month_filter}")
    
    filter_str = "_".join(filter_parts)
    filename = f"My_Payment_History_{filter_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

# CHAT ROUTES
@app.route('/chat/dashboard')
@login_required
def chat_dashboard():
    """Chat dashboard for users"""
    return render_template('chat_dashboard.html')

@app.route('/chat/conversation/<int:conversation_id>')
@login_required
def chat_conversation(conversation_id):
    """View specific chat conversation"""
    # For now, just render the template with a basic conversation structure
    return render_template('chat_conversation.html', conversation_id=conversation_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_database()  # Run migration to add new columns
        create_admin_user()
        create_default_settings()
    app.run(debug=True)
