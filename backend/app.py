from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
import calendar
from decimal import Decimal
from models import db, User, MeterReading, ElectricityBill, RentPayment, SystemSettings, Document, Notification, ChatMessage
from forms import (RegistrationForm, LoginForm, MeterReadingForm, RentAssignmentForm, 
                  SystemSettingsForm, PaymentForm, NotificationForm, PasswordResetForm, 
                  NewPasswordForm, EditRenterForm, ChatMessageForm)
import json
import io
import zipfile
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///billing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'Rent & Billing System <your-email@gmail.com>')

# Make calendar available in templates
app.jinja_env.globals['calendar'] = calendar

# Initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_email_notification(recipient_email, subject, message, notification_type):
    """Send email notification to user"""
    try:
        msg = Message(
            subject=f"[Rent & Billing] {subject}",
            recipients=[recipient_email],
            body=f"""
Dear Tenant,

You have received a new {notification_type} notification:

{message}

Best regards,
Rent & Billing Management System

---
This is an automated message. Please do not reply to this email.
If you have any questions, please contact the admin directly.
            """.strip()
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def create_admin_user():
    """Create default admin user"""
    admin = User.query.filter_by(email='ashraj77777@gmail.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='ashraj77777@gmail.com',
            password_hash=generate_password_hash('4129'),
            password_plain='4129',
            is_admin=True,
            is_approved=True  # Admin is auto-approved
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created")

def migrate_database():
    """Migrate database to add new columns"""
    try:
        # Check if new columns exist
        result = db.session.execute(db.text("PRAGMA table_info(notification)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add missing columns to notification table
        if 'email_sent' not in columns:
            db.session.execute(db.text("ALTER TABLE notification ADD COLUMN email_sent BOOLEAN DEFAULT 0"))
            print("Added email_sent column to notification table")
        
        if 'email_sent_at' not in columns:
            db.session.execute(db.text("ALTER TABLE notification ADD COLUMN email_sent_at DATETIME"))
            print("Added email_sent_at column to notification table")
        
        if 'enable_chat' not in columns:
            db.session.execute(db.text("ALTER TABLE notification ADD COLUMN enable_chat BOOLEAN DEFAULT 0"))
            print("Added enable_chat column to notification table")
        
        # Check if chat_message table exists, if not create it
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_message'"))
        if not result.fetchone():
            db.create_all()
            print("Created chat_message table")
        
        db.session.commit()
        print("Database migration completed successfully")
    except Exception as e:
        print(f"Database migration error: {e}")
        db.session.rollback()

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
    
    # Mark as paid (in real implementation, this would be handled by payment gateway)
    payment.is_paid = True
    payment.payment_date = datetime.now()
    payment.payment_method = request.form.get('payment_method', 'upi')
    payment.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    db.session.commit()
    flash('Payment successful!', 'success')
    
    return redirect(url_for('renter_dashboard'))

@app.route('/static/qr_code.jpeg')
def serve_qr_code():
    """Serve the static QR code image"""
    return send_file('../qr_code.jpeg', mimetype='image/jpeg')

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
    pending_verifications = ElectricityBill.query.filter_by(payment_status='pending').count()
    
    return render_template('admin_dashboard.html',
                         renters=renters,
                         total_rent_collection=total_rent_collection,
                         total_electricity_collection=total_electricity_collection,
                         pending_rent_payments=pending_rent_payments,
                         pending_electricity_bills=pending_electricity_bills,
                         pending_verifications=pending_verifications,
                         current_month=current_month)

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

@app.route('/admin/send_notification', methods=['GET', 'POST'])
@login_required
def send_notification():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    form = NotificationForm()
    
    # Populate renter choices for individual notifications
    renters = User.query.filter_by(is_admin=False, is_active=True).all()
    form.recipient_id.choices = [(0, 'Select a renter')] + [(r.id, f"{r.username} - Room {r.room_number}") for r in renters]
    
    if form.validate_on_submit():
        recipients = []
        
        if form.recipient_type.data == 'all':
            # Send to all active renters
            recipients = User.query.filter_by(is_admin=False, is_active=True).all()
        elif form.recipient_type.data == 'individual':
            # Send to specific renter
            if form.recipient_id.data and form.recipient_id.data > 0:
                recipient = User.query.get(form.recipient_id.data)
                if recipient:
                    recipients = [recipient]
            else:
                flash('Please select a renter for individual notification.', 'error')
                return render_template('send_notification.html', form=form)
        
        sent_count = 0
        email_sent_count = 0
        
        for renter in recipients:
            # Create notification
            notification = Notification(
                renter_id=renter.id,
                message=form.message.data,
                notification_type=form.notification_type.data,
                enable_chat=form.enable_chat.data,
                email_sent=False
            )
            db.session.add(notification)
            db.session.flush()  # Get the notification ID
            
            # Send email if requested
            if form.send_email.data:
                email_subject = f"{form.notification_type.data.title()} Notification"
                if send_email_notification(renter.email, email_subject, form.message.data, form.notification_type.data):
                    notification.email_sent = True
                    notification.email_sent_at = datetime.now()
                    email_sent_count += 1
            
            sent_count += 1
        
        db.session.commit()
        
        if form.recipient_type.data == 'all':
            flash(f'Notification sent to {sent_count} renters! Emails sent: {email_sent_count}', 'success')
        else:
            flash(f'Notification sent to {recipients[0].username}! Email sent: {"Yes" if email_sent_count > 0 else "No"}', 'success')
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('send_notification.html', form=form)

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
    
    return render_template('view_renter.html',
                         renter=renter,
                         rent_payments=rent_payments,
                         electricity_bills=electricity_bills,
                         meter_readings=meter_readings)

# Admin CRUD Operations for Bills
@app.route('/admin/delete_electricity_bill/<int:bill_id>')
@login_required
def delete_electricity_bill(bill_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    renter_id = bill.renter_id
    
    # Also delete the associated meter reading
    meter_reading = MeterReading.query.get(bill.meter_reading_id)
    if meter_reading:
        db.session.delete(meter_reading)
    
    db.session.delete(bill)
    db.session.commit()
    flash('Electricity bill deleted successfully!', 'success')
    return redirect(url_for('view_renter', renter_id=renter_id))

@app.route('/admin/delete_rent_payment/<int:payment_id>')
@login_required
def delete_rent_payment(payment_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    payment = RentPayment.query.get_or_404(payment_id)
    renter_id = payment.renter_id
    
    db.session.delete(payment)
    db.session.commit()
    flash('Rent payment deleted successfully!', 'success')
    return redirect(url_for('view_renter', renter_id=renter_id))

@app.route('/admin/edit_electricity_bill/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_electricity_bill(bill_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    
    if request.method == 'POST':
        units_consumed = float(request.form.get('units_consumed'))
        rate_per_unit = float(request.form.get('rate_per_unit'))
        fixed_charge = float(request.form.get('fixed_charge'))
        
        bill.units_consumed = units_consumed
        bill.rate_per_unit = rate_per_unit
        bill.fixed_charge = fixed_charge
        bill.total_amount = (units_consumed * rate_per_unit) + fixed_charge
        
        # Update associated meter reading
        meter_reading = MeterReading.query.get(bill.meter_reading_id)
        if meter_reading:
            meter_reading.units_consumed = units_consumed
        
        db.session.commit()
        flash('Electricity bill updated successfully!', 'success')
        return redirect(url_for('view_renter', renter_id=bill.renter_id))
    
    return render_template('edit_electricity_bill.html', bill=bill)

@app.route('/admin/edit_rent_payment/<int:payment_id>', methods=['GET', 'POST'])
@login_required
def edit_rent_payment(payment_id):
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    payment = RentPayment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        payment.amount = Decimal(str(request.form.get('amount')))
        payment.month = int(request.form.get('month'))
        payment.year = int(request.form.get('year'))
        payment.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Rent payment updated successfully!', 'success')
        return redirect(url_for('view_renter', renter_id=payment.renter_id))
    
    return render_template('edit_rent_payment.html', payment=payment)

@app.route('/admin/bills')
@login_required
def admin_bills():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get all bills
    electricity_bills = ElectricityBill.query.join(User).order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
    rent_payments = RentPayment.query.join(User).order_by(RentPayment.year.desc(), RentPayment.month.desc()).all()
    
    return render_template('admin_bills.html', 
                         electricity_bills=electricity_bills,
                         rent_payments=rent_payments)

@app.route('/admin/reading_history')
@login_required
def admin_reading_history():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get all meter readings with renter information
    readings = MeterReading.query.join(User).order_by(MeterReading.year.desc(), MeterReading.month.desc()).all()
    
    # Group readings by renter
    readings_by_renter = {}
    for reading in readings:
        renter_id = reading.renter_id
        if renter_id not in readings_by_renter:
            readings_by_renter[renter_id] = {
                'renter': reading.renter,
                'readings': []
            }
        readings_by_renter[renter_id]['readings'].append(reading)
    
    return render_template('admin_reading_history.html', readings_by_renter=readings_by_renter)

@app.route('/admin/monthly_report')
@login_required
def admin_monthly_report():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    # Get monthly statistics
    from datetime import datetime
    from sqlalchemy import func, extract
    
    current_year = datetime.now().year
    
    # Monthly rent collection
    rent_stats = db.session.query(
        extract('month', RentPayment.created_at).label('month'),
        func.sum(RentPayment.amount).label('total_amount'),
        func.count(RentPayment.id).label('total_payments'
    )).filter(
        extract('year', RentPayment.created_at) == current_year,
        RentPayment.is_paid == True
    ).group_by(extract('month', RentPayment.created_at)).all()
    
    # Monthly electricity collection
    electricity_stats = db.session.query(
        extract('month', ElectricityBill.created_at).label('month'),
        func.sum(ElectricityBill.total_amount).label('total_amount'),
        func.count(ElectricityBill.id).label('total_bills')
    ).filter(
        extract('year', ElectricityBill.created_at) == current_year,
        ElectricityBill.is_paid == True
    ).group_by(extract('month', ElectricityBill.created_at)).all()
    
    # Pending payments
    pending_rent = RentPayment.query.filter_by(is_paid=False).count()
    pending_electricity = ElectricityBill.query.filter_by(is_paid=False).count()
    
    return render_template('admin_monthly_report.html',
                         rent_stats=rent_stats,
                         electricity_stats=electricity_stats,
                         pending_rent=pending_rent,
                         pending_electricity=pending_electricity,
                         current_year=current_year)

@app.route('/admin/auto_generate_bills', methods=['GET', 'POST'])
@login_required
def auto_generate_bills():
    if not current_user.is_admin:
        return redirect(url_for('renter_dashboard'))
    
    if request.method == 'POST':
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        
        # Generate rent payments for all active renters
        active_renters = User.query.filter_by(is_admin=False, is_active=True).all()
        generated_count = 0
        
        for renter in active_renters:
            existing_payment = RentPayment.query.filter_by(
                renter_id=renter.id,
                month=month,
                year=year
            ).first()
            
            if not existing_payment:
                rent_payment = create_monthly_rent_payment(renter, month, year)
                generated_count += 1
        
        db.session.commit()
        flash(f'Generated {generated_count} rent payments for {calendar.month_name[month]} {year}', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('auto_generate_bills.html')

@app.route('/admin/get_previous_reading')
@login_required
def get_previous_reading():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    renter_id = request.args.get('renter_id')
    if not renter_id:
        return jsonify({'error': 'Renter ID required'}), 400
    
    # Get the latest reading for this renter
    previous_reading = MeterReading.query.filter_by(
        renter_id=renter_id
    ).order_by(MeterReading.year.desc(), MeterReading.month.desc()).first()
    
    if previous_reading:
        return jsonify({
            'previous_reading': previous_reading.current_reading,
            'month': previous_reading.month,
            'year': previous_reading.year
        })
    else:
        return jsonify({'previous_reading': 0})

# New routes for user electricity bill payment
@app.route('/renter/electricity_bills')
@login_required
def renter_electricity_bills():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get all electricity bills for this renter
    bills = ElectricityBill.query.filter_by(renter_id=current_user.id).order_by(
        ElectricityBill.year.desc(), ElectricityBill.month.desc()
    ).all()
    
    return render_template('renter_electricity_bills.html', bills=bills)

@app.route('/renter/pay_electricity/<int:bill_id>')
@login_required
def pay_electricity_bill(bill_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('renter_dashboard'))
    
    # Get current electricity rate
    settings = SystemSettings.query.first()
    rate_per_unit = settings.electricity_rate if settings else 8.0
    
    return render_template('pay_electricity.html', bill=bill, rate_per_unit=rate_per_unit)

@app.route('/renter/process_electricity_payment/<int:bill_id>', methods=['POST'])
@login_required
def process_electricity_payment(bill_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('renter_dashboard'))
    
    payment_type = request.form.get('payment_type')
    
    if payment_type == 'full':
        # Pay full amount
        amount_to_pay = bill.total_amount
        units_paid = bill.units_consumed
        
        bill.is_paid = True
        bill.payment_date = datetime.now()
        bill.payment_method = 'upi'
        bill.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
    elif payment_type == 'partial':
        # Pay for custom units
        units_to_pay = int(request.form.get('units_to_pay'))
        
        # Validate unit limits
        if units_to_pay > 1000:
            flash('Cannot pay for more than 1000 units at a time.', 'error')
            return redirect(url_for('pay_electricity_bill', bill_id=bill_id))
        
        if units_to_pay > bill.remaining_units:
            flash('Cannot pay for more units than remaining.', 'error')
            return redirect(url_for('pay_electricity_bill', bill_id=bill_id))
        
        settings = SystemSettings.query.first()
        rate_per_unit = Decimal(str(settings.electricity_rate)) if settings else Decimal('8.0')
        
        amount_to_pay = Decimal(str(units_to_pay)) * rate_per_unit
        units_paid = Decimal(str(units_to_pay))
        
        # Update bill with partial payment
        if not hasattr(bill, 'units_paid'):
            bill.units_paid = Decimal('0')
        if not hasattr(bill, 'amount_paid'):
            bill.amount_paid = Decimal('0')
            
        bill.units_paid = (bill.units_paid or Decimal('0')) + units_paid
        bill.amount_paid = (bill.amount_paid or Decimal('0')) + amount_to_pay
        
        # Check if fully paid
        if bill.units_paid >= bill.units_consumed:
            bill.is_paid = True
            bill.payment_date = datetime.now()
            bill.payment_method = 'upi'
            bill.transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    db.session.commit()
    
    # Generate QR code URL for payment
    upi_url = f"upi://pay?pa=7677242570@ybl&pn=Electricity Bill&am={amount_to_pay}&cu=INR&tn=Electricity Bill Payment for {units_paid} units"
    
    return render_template('electricity_payment_qr.html', 
                         bill=bill, 
                         amount_to_pay=amount_to_pay,
                         units_paid=units_paid,
                         upi_url=upi_url)

@app.route('/renter/confirm_electricity_payment/<int:bill_id>', methods=['POST'])
@login_required
def confirm_electricity_payment(bill_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('renter_dashboard'))
    
    # Mark payment as confirmed
    flash('Payment confirmed successfully!', 'success')
    return redirect(url_for('renter_electricity_bills'))

@app.route('/admin/get_previous_reading/<int:renter_id>')
@login_required
def get_previous_reading_by_renter(renter_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get the most recent reading for this renter
    previous_reading = MeterReading.query.filter_by(
        renter_id=renter_id
    ).order_by(MeterReading.year.desc(), MeterReading.month.desc()).first()
    
    if previous_reading:
        return jsonify({
            'previous_reading': float(previous_reading.current_reading),
            'month': previous_reading.month,
            'year': previous_reading.year
        })
    else:
        return jsonify({'previous_reading': None})

@app.route('/renter/upload_payment_receipt/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def upload_payment_receipt(bill_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('renter_dashboard'))
    
    if request.method == 'POST':
        receipt_file = request.files.get('receipt')
        transaction_id = request.form.get('transaction_id')
        payment_notes = request.form.get('payment_notes')
        
        if not receipt_file or receipt_file.filename == '':
            flash('Please upload a payment receipt.', 'error')
            return redirect(request.url)
        
        # Check file size (5MB max)
        if receipt_file.content_length > 5 * 1024 * 1024:
            flash('File size too large. Maximum 5MB allowed.', 'error')
            return redirect(request.url)
        
        # Save receipt file
        import os
        from werkzeug.utils import secure_filename
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'receipts')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(receipt_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"receipt_{bill_id}_{timestamp}_{filename}"
        
        receipt_path = os.path.join(uploads_dir, filename)
        receipt_file.save(receipt_path)
        
        # Update bill with receipt information
        bill.payment_receipt = f'uploads/receipts/{filename}'
        bill.payment_status = 'pending'
        bill.transaction_id = transaction_id
        bill.verification_notes = payment_notes
        bill.payment_date = datetime.now()
        bill.payment_method = 'upi'
        
        db.session.commit()
        
        # Create notification for admin
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            notification = Notification(
                renter_id=current_user.id,
                message=f'Payment Receipt Uploaded: {current_user.username} uploaded payment receipt for {calendar.month_name[bill.month]} {bill.year} electricity bill (₹{bill.amount_paid})',
                notification_type='payment_receipt'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash('Payment receipt uploaded successfully! Your payment is now pending admin verification.', 'success')
        return redirect(url_for('renter_electricity_bills'))
    
    # Calculate amounts for display
    units_paid = request.args.get('units_paid', bill.units_paid or 0, type=float)
    amount_paid = request.args.get('amount_paid', bill.amount_paid or 0, type=float)
    
    return render_template('upload_payment_receipt.html', 
                         bill=bill, 
                         units_paid=units_paid,
                         amount_paid=amount_paid)

@app.route('/admin/verify_payment/<int:bill_id>/<action>')
@login_required
def verify_payment(bill_id, action):
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    
    if action == 'approve':
        bill.payment_status = 'approved'
        bill.is_paid = True
        bill.verification_date = datetime.now()
        bill.verified_by = current_user.id
        
        # Create notification for renter
        notification = Notification(
            renter_id=bill.renter_id,
            message=f'Payment Approved: Your payment for {calendar.month_name[bill.month]} {bill.year} electricity bill has been approved by admin.',
            notification_type='payment_approved'
        )
        db.session.add(notification)
        
        flash('Payment approved successfully!', 'success')
        
    elif action == 'reject':
        bill.payment_status = 'rejected'
        bill.verification_date = datetime.now()
        bill.verified_by = current_user.id
        
        # Create notification for renter
        notification = Notification(
            renter_id=bill.renter_id,
            message=f'Payment Rejected: Your payment for {calendar.month_name[bill.month]} {bill.year} electricity bill has been rejected. Please contact admin for details.',
            notification_type='payment_rejected'
        )
        db.session.add(notification)
        
        flash('Payment rejected.', 'warning')
    
    db.session.commit()
    return redirect(url_for('admin_pending_payments'))

@app.route('/admin/pending_payments')
@login_required
def admin_pending_payments():
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    pending_payments = ElectricityBill.query.filter_by(payment_status='pending').order_by(ElectricityBill.payment_date.desc()).all()
    
    return render_template('admin_pending_payments.html', pending_payments=pending_payments)

@app.route('/api/check_payment_status/<int:bill_id>')
@login_required
def check_payment_status(bill_id):
    """API endpoint to check if payment has been completed"""
    if current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Admin access not allowed'})
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    # Check payment status
    if bill.payment_status == 'approved':
        return jsonify({
            'status': 'completed',
            'message': 'Payment verified and approved',
            'amount': float(bill.amount_paid or 0),
            'units': float(bill.units_paid or 0)
        })
    elif bill.payment_status == 'pending':
        return jsonify({
            'status': 'pending',
            'message': 'Payment submitted, awaiting verification'
        })
    elif bill.payment_status == 'rejected':
        return jsonify({
            'status': 'rejected',
            'message': 'Payment was rejected'
        })
    else:
        return jsonify({
            'status': 'unpaid',
            'message': 'No payment detected yet'
        })

@app.route('/api/simulate_payment/<int:bill_id>', methods=['POST'])
@login_required
def simulate_payment(bill_id):
    """API endpoint to simulate payment completion (for testing)"""
    if current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Admin access not allowed'})
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    # Simulate payment completion
    bill.payment_status = 'approved'
    bill.is_paid = True
    bill.payment_date = datetime.now()
    bill.payment_method = 'upi'
    bill.transaction_id = f"SIM{datetime.now().strftime('%Y%m%d%H%M%S')}"
    bill.verification_date = datetime.now()
    bill.verified_by = 1  # Admin user ID
    
    # Create success notification
    notification = Notification(
        renter_id=current_user.id,
        message=f'Payment Successful: Your payment of ₹{bill.amount_paid} for {calendar.month_name[bill.month]} {bill.year} electricity bill has been successfully processed.',
        notification_type='payment_success'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Payment simulated successfully',
        'redirect_url': url_for('renter_dashboard')
    })

@app.route('/webhook/payment_notification', methods=['POST'])
def payment_webhook():
    """Webhook endpoint for real payment gateway notifications"""
    try:
        data = request.get_json()
        
        # Validate webhook signature (in production)
        # if not validate_webhook_signature(data):
        #     return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401
        
        transaction_id = data.get('transaction_id')
        amount = data.get('amount')
        status = data.get('status')
        upi_ref = data.get('upi_ref')
        
        # Find the bill by transaction reference
        bill = ElectricityBill.query.filter_by(transaction_id=transaction_id).first()
        
        if not bill:
            return jsonify({'status': 'error', 'message': 'Bill not found'}), 404
        
        if status == 'SUCCESS':
            # Payment successful
            bill.payment_status = 'approved'
            bill.is_paid = True
            bill.payment_date = datetime.now()
            bill.payment_method = 'upi'
            bill.transaction_id = upi_ref
            bill.verification_date = datetime.now()
            bill.verified_by = 1  # System verification
            
            # Create notification for user
            notification = Notification(
                renter_id=bill.renter_id,
                message=f'Payment Successful: Your payment of ₹{amount} for electricity bill has been successfully processed.',
                notification_type='payment_success'
            )
            db.session.add(notification)
            
        elif status == 'FAILED':
            # Payment failed
            bill.payment_status = 'rejected'
            
            # Create notification for user
            notification = Notification(
                renter_id=bill.renter_id,
                message=f'Payment Failed: Your payment of ₹{amount} for electricity bill has failed. Please try again.',
                notification_type='payment_failed'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Webhook processed'})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': 'Webhook processing failed'}), 500

@app.route('/api/payment_intent/<int:bill_id>', methods=['POST'])
@login_required
def create_payment_intent(bill_id):
    """Create payment intent for real payment gateway integration"""
    if current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Admin access not allowed'})
    
    bill = ElectricityBill.query.get_or_404(bill_id)
    if bill.renter_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'})
    
    # Calculate amount from form data
    units_to_pay = float(request.json.get('units_to_pay', 0))
    if units_to_pay <= 0:
        return jsonify({'status': 'error', 'message': 'Invalid units'})
    
    settings = SystemSettings.query.first()
    rate_per_unit = float(settings.electricity_rate) if settings else 8.0
    amount_to_pay = units_to_pay * rate_per_unit
    
    # Generate unique transaction ID
    transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{bill.id}"
    
    # In production, this would integrate with payment gateway
    # For now, return UPI URL and transaction details
    upi_url = f"upi://pay?pa=7677242570@ybl&pn=Electricity Bill&am={amount_to_pay}&cu=INR&tn=Bill Payment&tr={transaction_id}"
    
    return jsonify({
        'status': 'success',
        'transaction_id': transaction_id,
        'amount': amount_to_pay,
        'units': units_to_pay,
        'upi_url': upi_url,
        'webhook_url': url_for('payment_webhook', _external=True)
    })

# Helper functions for generating reports and downloads

def generate_reading_pdf(readings, user):
    """Generate PDF report for reading history"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>Meter Reading History - {user.username}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # User info
    user_info = Paragraph(f"<b>Room:</b> {user.room_number}<br/><b>Email:</b> {user.email}", styles['Normal'])
    story.append(user_info)
    story.append(Spacer(1, 20))
    
    # Table data
    data = [['Month/Year', 'Date', 'Previous', 'Current', 'Units', 'Status']]
    
    for reading in readings:
        # Get the electricity bill for this reading (there should be one)
        electricity_bill = next((bill for bill in reading.electricity_bills), None)
        status = 'Paid' if electricity_bill and electricity_bill.is_paid else 'Pending'
        data.append([
            f"{calendar.month_name[reading.month]} {reading.year}",
            reading.reading_date.strftime('%d/%m/%Y'),
            f"{reading.previous_reading:.2f}",
            f"{reading.current_reading:.2f}",
            f"{reading.units_consumed:.2f}",
            status
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'reading_history_{user.username}.pdf',
        mimetype='application/pdf'
    )

def generate_reading_excel(readings, user):
    """Generate Excel report for reading history"""
    buffer = io.BytesIO()
    
    # Create DataFrame
    data = []
    for reading in readings:
        # Get the electricity bill for this reading (there should be one)
        electricity_bill = next((bill for bill in reading.electricity_bills), None)
        status = 'Paid' if electricity_bill and electricity_bill.is_paid else 'Pending'
        data.append({
            'Month/Year': f"{calendar.month_name[reading.month]} {reading.year}",
            'Date': reading.reading_date.strftime('%d/%m/%Y'),
            'Previous Reading': float(reading.previous_reading),
            'Current Reading': float(reading.current_reading),
            'Units Consumed': float(reading.units_consumed),
            'Status': status
        })
    
    df = pd.DataFrame(data)
    
    # Write to Excel
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Reading History', index=False)
        
        # Add summary sheet
        summary_data = {
            'Total Readings': len(readings),
            'Total Units': sum(float(r.units_consumed) for r in readings),
            'Average Monthly': sum(float(r.units_consumed) for r in readings) / len(readings) if readings else 0,
            'Latest Reading': float(readings[0].current_reading) if readings else 0
        }
        
        summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'reading_history_{user.username}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def generate_receipts_zip(user):
    """Generate ZIP file containing all payment receipts"""
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Get all electricity bills with receipts
        electricity_bills = ElectricityBill.query.filter_by(renter_id=user.id).all()
        
        for bill in electricity_bills:
            if bill.payment_receipt:
                receipt_path = os.path.join(app.root_path, 'static', bill.payment_receipt)
                if os.path.exists(receipt_path):
                    filename = f"electricity_{calendar.month_name[bill.month]}_{bill.year}_{bill.payment_receipt.split('/')[-1]}"
                    zip_file.write(receipt_path, filename)
        
        # Get all rent payments with receipts (if any)
        rent_payments = RentPayment.query.filter_by(renter_id=user.id).all()
        
        for payment in rent_payments:
            if hasattr(payment, 'payment_receipt') and payment.payment_receipt:
                receipt_path = os.path.join(app.root_path, 'static', payment.payment_receipt)
                if os.path.exists(receipt_path):
                    filename = f"rent_{calendar.month_name[payment.month]}_{payment.year}_{payment.payment_receipt.split('/')[-1]}"
                    zip_file.write(receipt_path, filename)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'payment_receipts_{user.username}.zip',
        mimetype='application/zip'
    )

def generate_payment_data_excel(user):
    """Generate Excel file with all payment data"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Electricity payments
        electricity_bills = ElectricityBill.query.filter_by(renter_id=user.id).order_by(ElectricityBill.year.desc(), ElectricityBill.month.desc()).all()
        
        electricity_data = []
        for bill in electricity_bills:
            electricity_data.append({
                'Month/Year': f"{calendar.month_name[bill.month]} {bill.year}",
                'Payment Date': bill.payment_date.strftime('%d/%m/%Y %H:%M') if bill.payment_date else '',
                'Units Consumed': float(bill.units_consumed),
                'Units Paid': float(bill.units_paid or 0),
                'Total Amount': float(bill.total_amount),
                'Amount Paid': float(bill.amount_paid or 0),
                'Rate per Unit': float(bill.rate_per_unit),
                'Payment Status': bill.payment_status or 'unpaid',
                'Transaction ID': bill.transaction_id or '',
                'Payment Method': bill.payment_method or ''
            })
        
        if electricity_data:
            df_electricity = pd.DataFrame(electricity_data)
            df_electricity.to_excel(writer, sheet_name='Electricity Bills', index=False)
        
        # Rent payments
        rent_payments = RentPayment.query.filter_by(renter_id=user.id).order_by(RentPayment.year.desc(), RentPayment.month.desc()).all()
        
        rent_data = []
        for payment in rent_payments:
            rent_data.append({
                'Month/Year': f"{calendar.month_name[payment.month]} {payment.year}",
                'Payment Date': payment.payment_date.strftime('%d/%m/%Y %H:%M') if payment.payment_date else '',
                'Amount': float(payment.amount),
                'Due Date': payment.due_date.strftime('%d/%m/%Y'),
                'Is Paid': payment.is_paid,
                'Is Overdue': payment.is_overdue,
                'Transaction ID': payment.transaction_id or '',
                'Payment Method': payment.payment_method or ''
            })
        
        if rent_data:
            df_rent = pd.DataFrame(rent_data)
            df_rent.to_excel(writer, sheet_name='Rent Payments', index=False)
        
        # Summary
        summary_data = {
            'Total Electricity Bills': len(electricity_bills),
            'Total Rent Payments': len(rent_payments),
            'Total Electricity Amount': sum(float(bill.amount_paid or 0) for bill in electricity_bills),
            'Total Rent Amount': sum(float(payment.amount) for payment in rent_payments if payment.is_paid),
            'Pending Electricity Bills': len([b for b in electricity_bills if b.payment_status == 'pending']),
            'Pending Rent Payments': len([p for p in rent_payments if not p.is_paid])
        }
        
        summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'payment_data_{user.username}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def generate_individual_receipt(payment, payment_type):
    """Generate individual payment receipt as PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>Payment Receipt - {payment_type.replace('Bill', ' Bill')}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Receipt details
    receipt_data = [
        ['Receipt No:', f"RCP{payment.id:06d}"],
        ['Date:', payment.payment_date.strftime('%d/%m/%Y %H:%M') if payment.payment_date else 'N/A'],
        ['Month/Year:', f"{calendar.month_name[payment.month]} {payment.year}"],
        ['Renter:', payment.renter.username],
        ['Room:', payment.renter.room_number],
    ]
    
    if payment_type == 'ElectricityBill':
        receipt_data.extend([
            ['Units Consumed:', f"{payment.units_consumed:.2f}"],
            ['Units Paid:', f"{payment.units_paid:.2f}" if payment.units_paid else "0.00"],
            ['Rate per Unit:', f"₹{payment.rate_per_unit:.2f}"],
            ['Total Amount:', f"₹{payment.total_amount:.2f}"],
            ['Amount Paid:', f"₹{payment.amount_paid:.2f}" if payment.amount_paid else "₹0.00"],
        ])
    else:
        receipt_data.extend([
            ['Amount:', f"₹{payment.amount:.2f}"],
            ['Due Date:', payment.due_date.strftime('%d/%m/%Y')],
        ])
    
    receipt_data.extend([
        ['Transaction ID:', payment.transaction_id or 'N/A'],
        ['Payment Method:', payment.payment_method or 'N/A'],
        ['Status:', 'Paid' if payment.is_paid else 'Pending'],
    ])
    
    # Create table
    table = Table(receipt_data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Footer
    footer = Paragraph("<i>This is a computer-generated receipt.</i>", styles['Normal'])
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'receipt_{payment_type}_{payment.id}.pdf',
        mimetype='application/pdf'
    )

# Chat Routes
@app.route('/chat')
@login_required
def chat_dashboard():
    """Main chat dashboard"""
    if current_user.is_admin:
        # Admin sees all active conversations
        conversations = db.session.query(ChatMessage.recipient_id, User.username, User.room_number)\
            .join(User, ChatMessage.recipient_id == User.id)\
            .filter(ChatMessage.sender_id == current_user.id)\
            .distinct(ChatMessage.recipient_id)\
            .all()
        
        # Also get conversations where admin is recipient
        renter_conversations = db.session.query(ChatMessage.sender_id, User.username, User.room_number)\
            .join(User, ChatMessage.sender_id == User.id)\
            .filter(ChatMessage.recipient_id == current_user.id)\
            .distinct(ChatMessage.sender_id)\
            .all()
        
        # Combine and deduplicate
        all_conversations = {}
        for conv in conversations:
            all_conversations[conv[0]] = {'username': conv[1], 'room_number': conv[2]}
        for conv in renter_conversations:
            all_conversations[conv[0]] = {'username': conv[1], 'room_number': conv[2]}
            
        return render_template('chat_dashboard.html', conversations=all_conversations)
    else:
        # Renter only sees admin chat
        admin_user = User.query.filter_by(is_admin=True).first()
        if admin_user:
            return redirect(url_for('chat_conversation', user_id=admin_user.id))
        else:
            flash('No admin available for chat.', 'error')
            return redirect(url_for('renter_dashboard'))

@app.route('/chat/<int:user_id>')
@login_required
def chat_conversation(user_id):
    """View chat conversation with specific user"""
    other_user = User.query.get_or_404(user_id)
    
    # Get chat messages between current user and other user
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark messages as read where current user is recipient
    unread_messages = ChatMessage.query.filter(
        ChatMessage.sender_id == user_id,
        ChatMessage.recipient_id == current_user.id,
        ChatMessage.is_read == False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    form = ChatMessageForm()
    
    return render_template('chat_conversation.html', 
                         other_user=other_user, 
                         messages=messages, 
                         form=form)

@app.route('/chat/<int:user_id>/send', methods=['POST'])
@login_required
def send_chat_message(user_id):
    """Send a chat message"""
    other_user = User.query.get_or_404(user_id)
    form = ChatMessageForm()
    
    if form.validate_on_submit():
        message = ChatMessage(
            sender_id=current_user.id,
            recipient_id=user_id,
            message=form.message.data
        )
        db.session.add(message)
        db.session.commit()
        
        flash('Message sent successfully!', 'success')
    else:
        flash('Failed to send message. Please check your input.', 'error')
    
    return redirect(url_for('chat_conversation', user_id=user_id))

@app.route('/api/chat/unread_count')
@login_required
def get_unread_chat_count():
    """Get count of unread chat messages"""
    unread_count = ChatMessage.query.filter(
        ChatMessage.recipient_id == current_user.id,
        ChatMessage.is_read == False
    ).count()
    
    return jsonify({'unread_count': unread_count})

@app.route('/chat/notification/<int:notification_id>')
@login_required
def chat_from_notification(notification_id):
    """Start chat from a notification"""
    notification = Notification.query.get_or_404(notification_id)
    
    if not notification.enable_chat:
        flash('Chat is not enabled for this notification.', 'error')
        return redirect(url_for('renter_notifications'))
    
    if current_user.is_admin:
        # Admin chatting with renter
        other_user_id = notification.renter_id
    else:
        # Renter chatting with admin
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            flash('No admin available for chat.', 'error')
            return redirect(url_for('renter_notifications'))
        other_user_id = admin_user.id
    
    return redirect(url_for('chat_conversation', user_id=other_user_id))

# Debug route to check pending payments
@app.route('/debug/pending_payments')
@login_required
def debug_pending_payments():
    if not current_user.is_admin:
        return "Admin access required"
    
    pending_payments = ElectricityBill.query.filter_by(payment_status='pending').all()
    all_bills = ElectricityBill.query.all()
    
    debug_info = {
        'total_bills': len(all_bills),
        'pending_count': len(pending_payments),
        'pending_bills': []
    }
    
    for bill in pending_payments:
        debug_info['pending_bills'].append({
            'id': bill.id,
            'renter': bill.renter.username,
            'month': bill.month,
            'year': bill.year,
            'status': bill.payment_status,
            'amount_paid': float(bill.amount_paid or 0),
            'receipt': bill.payment_receipt
        })
    
    return f"<pre>{debug_info}</pre>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_database()  # Run migration to add new columns
        create_admin_user()
        create_default_settings()
    app.run(debug=True)
