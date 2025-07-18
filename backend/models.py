from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from decimal import Decimal

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    password_plain = db.Column(db.String(255), nullable=True)  # For admin override
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval required
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Renter specific fields
    rent_amount = db.Column(db.Numeric(10, 2), default=0.0)
    room_number = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    
    # Profile fields
    profile_picture = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    aadhar_number = db.Column(db.String(20), nullable=True)
    pan_number = db.Column(db.String(20), nullable=True)
    profile_completion = db.Column(db.Integer, default=0)  # Percentage of profile completed
    document_verification_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    
    # Relationships
    meter_readings = db.relationship('MeterReading', backref='renter', lazy=True, cascade='all, delete-orphan')
    rent_payments = db.relationship('RentPayment', foreign_keys='RentPayment.renter_id', backref='renter', lazy=True, cascade='all, delete-orphan')
    electricity_bills = db.relationship('ElectricityBill', foreign_keys='ElectricityBill.renter_id', backref='renter', lazy=True, cascade='all, delete-orphan')
    verified_payments = db.relationship('ElectricityBill', foreign_keys='ElectricityBill.verified_by', backref='verifier', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class MeterReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_reading = db.Column(db.Numeric(10, 2), nullable=False)
    previous_reading = db.Column(db.Numeric(10, 2), default=0.0)
    units_consumed = db.Column(db.Numeric(10, 2), nullable=False)
    reading_date = db.Column(db.Date, default=date.today)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to electricity bills (one-to-many)
    electricity_bills = db.relationship('ElectricityBill', backref='meter_reading', lazy=True)
    
    def __repr__(self):
        return f'<MeterReading {self.renter.username} - {self.month}/{self.year}>'

class ElectricityBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meter_reading_id = db.Column(db.Integer, db.ForeignKey('meter_reading.id'), nullable=False)
    units_consumed = db.Column(db.Numeric(10, 2), nullable=False)
    rate_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    fixed_charge = db.Column(db.Numeric(10, 2), default=0.0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Partial payment fields
    units_paid = db.Column(db.Numeric(10, 2), default=0.0)
    amount_paid = db.Column(db.Numeric(10, 2), default=0.0)
    payment_method = db.Column(db.String(50), nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)
    
    # Payment verification fields
    payment_receipt = db.Column(db.String(255), nullable=True)  # Receipt file path
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, pending, approved, rejected
    verification_date = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    
    @property
    def remaining_units(self):
        return Decimal(str(self.units_consumed)) - Decimal(str(self.units_paid or 0))
    
    @property
    def remaining_amount(self):
        return Decimal(str(self.total_amount)) - Decimal(str(self.amount_paid or 0))
    
    def __repr__(self):
        return f'<ElectricityBill {self.renter.username} - {self.month}/{self.year}>'

class RentPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    is_paid = db.Column(db.Boolean, default=False)
    is_overdue = db.Column(db.Boolean, default=False)
    payment_method = db.Column(db.String(50), nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Payment verification fields
    payment_receipt = db.Column(db.String(255), nullable=True)  # Receipt file path
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, pending, approved, rejected
    verification_date = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_rent_payments')
    
    def __repr__(self):
        return f'<RentPayment {self.renter.username} - {self.month}/{self.year}>'

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    electricity_rate = db.Column(db.Numeric(10, 2), default=5.0)
    fixed_charge = db.Column(db.Numeric(10, 2), default=100.0)
    rent_due_date = db.Column(db.Integer, default=5)  # Day of month
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # reminder, overdue, announcement
    is_read = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    enable_chat = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    renter = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.notification_type}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    notification = db.relationship('Notification', backref='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage from {self.sender.username} to {self.recipient.username}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # profile_picture, aadhar_card, agreement_paper, other
    filename = db.Column(db.String(255), nullable=False)  # Stored filename
    original_filename = db.Column(db.String(255), nullable=False)  # Original filename
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    verification_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='documents')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_documents')
    
    def __repr__(self):
        return f'<Document {self.document_type} - {self.user.username}>'

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    nationality = db.Column(db.String(50), nullable=True)
    marital_status = db.Column(db.String(20), nullable=True)
    
    # Address Information
    permanent_address = db.Column(db.Text, nullable=True)
    current_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    
    # Contact Information
    phone = db.Column(db.String(20), nullable=True)
    alternate_phone = db.Column(db.String(20), nullable=True)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_relationship = db.Column(db.String(50), nullable=True)
    emergency_contact_address = db.Column(db.Text, nullable=True)
    
    # Professional Information
    occupation = db.Column(db.String(100), nullable=True)
    employer = db.Column(db.String(100), nullable=True)
    company_name = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    work_address = db.Column(db.Text, nullable=True)
    annual_income = db.Column(db.Numeric(12, 2), nullable=True)
    monthly_income = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Additional Information
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Previous Address (for reference)
    previous_address = db.Column(db.Text, nullable=True)
    previous_landlord_name = db.Column(db.String(100), nullable=True)
    previous_landlord_contact = db.Column(db.String(20), nullable=True)
    
    # Agreement Details
    lease_start_date = db.Column(db.Date, nullable=True)
    lease_end_date = db.Column(db.Date, nullable=True)
    security_deposit = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Profile Status
    profile_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('profile', uselist=False))
    
    def __repr__(self):
        return f'<UserProfile {self.user.username}>'
