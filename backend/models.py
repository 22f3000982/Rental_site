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
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Renter specific fields
    rent_amount = db.Column(db.Numeric(10, 2), default=0.0)
    room_number = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Relationships
    meter_readings = db.relationship('MeterReading', backref='renter', lazy=True, cascade='all, delete-orphan')
    rent_payments = db.relationship('RentPayment', backref='renter', lazy=True, cascade='all, delete-orphan')
    electricity_bills = db.relationship('ElectricityBill', foreign_keys='ElectricityBill.renter_id', backref='renter', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='renter', lazy=True, cascade='all, delete-orphan')
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

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # ID, Agreement, etc.
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.filename}>'

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
