from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, DecimalField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=20, message='Username must be between 4 and 20 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Phone number must be between 10 and 15 characters.')
    ])
    room_number = StringField('Room Number', validators=[
        DataRequired(),
        Length(min=1, max=20, message='Room number must be between 1 and 20 characters.')
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class MeterReadingForm(FlaskForm):
    renter_id = SelectField('Renter', coerce=int, validators=[DataRequired()])
    current_reading = DecimalField('Current Reading', validators=[
        DataRequired(),
        NumberRange(min=0, message='Reading must be positive')
    ])
    month = SelectField('Month', coerce=int, validators=[DataRequired()], choices=[
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ])
    year = IntegerField('Year', validators=[
        DataRequired(),
        NumberRange(min=2020, max=2030, message='Year must be between 2020 and 2030')
    ])
    submit = SubmitField('Add Reading')

class RentAssignmentForm(FlaskForm):
    renter_id = SelectField('Renter', coerce=int, validators=[DataRequired()])
    rent_amount = DecimalField('Rent Amount', validators=[
        DataRequired(),
        NumberRange(min=0, message='Rent amount must be positive')
    ])
    submit = SubmitField('Update Rent')

class SystemSettingsForm(FlaskForm):
    electricity_rate = DecimalField('Electricity Rate per Unit', validators=[
        DataRequired(),
        NumberRange(min=0, message='Rate must be positive')
    ])
    fixed_charge = DecimalField('Fixed Charge', validators=[
        DataRequired(),
        NumberRange(min=0, message='Fixed charge must be positive')
    ])
    rent_due_date = IntegerField('Rent Due Date (Day of Month)', validators=[
        DataRequired(),
        NumberRange(min=1, max=31, message='Due date must be between 1 and 31')
    ])
    submit = SubmitField('Update Settings')

class PaymentForm(FlaskForm):
    payment_method = SelectField('Payment Method', choices=[
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('netbanking', 'Net Banking'),
        ('cash', 'Cash')
    ], validators=[DataRequired()])
    submit = SubmitField('Pay Now')

class HistoricalRentPaymentForm(FlaskForm):
    renter_id = SelectField('Renter', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Rent Amount', validators=[
        DataRequired(),
        NumberRange(min=0, message='Amount must be positive')
    ])
    month = SelectField('Month', coerce=int, validators=[DataRequired()], choices=[
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ])
    year = IntegerField('Year', validators=[
        DataRequired(),
        NumberRange(min=2020, max=2030, message='Year must be between 2020 and 2030')
    ])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('netbanking', 'Net Banking'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer')
    ], validators=[DataRequired()])
    transaction_id = StringField('Transaction ID/Reference', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Historical Payment')

class HistoricalElectricityPaymentForm(FlaskForm):
    renter_id = SelectField('Renter', coerce=int, validators=[DataRequired()])
    current_reading = DecimalField('Current Reading', validators=[
        DataRequired(),
        NumberRange(min=0, message='Reading must be positive')
    ])
    previous_reading = DecimalField('Previous Reading', validators=[
        DataRequired(),
        NumberRange(min=0, message='Reading must be positive')
    ])
    units_consumed = DecimalField('Units Consumed', validators=[
        DataRequired(),
        NumberRange(min=0, message='Units must be positive')
    ])
    rate_per_unit = DecimalField('Rate per Unit', validators=[
        DataRequired(),
        NumberRange(min=0, message='Rate must be positive')
    ])
    total_amount = DecimalField('Total Amount', validators=[
        DataRequired(),
        NumberRange(min=0, message='Amount must be positive')
    ])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('netbanking', 'Net Banking'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Electricity Payment Record')

class CashPaymentForm(FlaskForm):
    payment_type = SelectField('Payment Type', choices=[
        ('rent', 'Rent Payment'),
        ('electricity', 'Electricity Payment')
    ], validators=[DataRequired()])
    amount = DecimalField('Amount Paid', validators=[
        DataRequired(),
        NumberRange(min=0, message='Amount must be positive')
    ])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    receipt_number = StringField('Receipt Number', validators=[Optional()])
    notes = TextAreaField('Payment Notes', validators=[Optional()])
    submit = SubmitField('Record Cash Payment')

class ChatMessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=1, max=1000, message='Message must be between 1 and 1000 characters.')
    ], widget=TextArea())
    submit = SubmitField('Send Message')

class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    submit = SubmitField('Reset Password')

class NewPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Update Password')

class EditRenterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=20, message='Username must be between 4 and 20 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Phone number must be between 10 and 15 characters.')
    ])
    room_number = StringField('Room Number', validators=[
        DataRequired(),
        Length(min=1, max=20, message='Room number must be between 1 and 20 characters.')
    ])
    rent_amount = DecimalField('Rent Amount', validators=[
        DataRequired(),
        NumberRange(min=0, message='Rent amount must be positive')
    ])
    electricity_bill_required = BooleanField('Electricity Bill Required')
    is_active = BooleanField('Active Status')
    is_approved = BooleanField('Approved Status')
    submit = SubmitField('Update Renter')

class UserProfileForm(FlaskForm):
    # Basic Information
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    
    # Password Change (Optional)
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    
    # Personal Information
    full_name = StringField('Full Name', validators=[
        Optional(),
        Length(max=100, message='Full name must be less than 100 characters.')
    ])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], validators=[Optional()])
    nationality = StringField('Nationality', validators=[
        Optional(),
        Length(max=50, message='Nationality must be less than 50 characters.')
    ])
    marital_status = SelectField('Marital Status', choices=[
        ('', 'Select Status'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ], validators=[Optional()])
    
    # Address Information
    permanent_address = TextAreaField('Permanent Address', validators=[Optional()])
    current_address = TextAreaField('Current Address', validators=[Optional()])
    city = StringField('City', validators=[
        Optional(),
        Length(max=50, message='City must be less than 50 characters.')
    ])
    state = StringField('State', validators=[
        Optional(),
        Length(max=50, message='State must be less than 50 characters.')
    ])
    postal_code = StringField('Postal Code', validators=[
        Optional(),
        Length(max=10, message='Postal code must be less than 10 characters.')
    ])
    country = StringField('Country', validators=[
        Optional(),
        Length(max=50, message='Country must be less than 50 characters.')
    ])
    
    # Contact Information
    alternate_phone = StringField('Alternate Phone', validators=[
        Optional(),
        Length(max=20, message='Phone number must be less than 20 characters.')
    ])
    whatsapp_number = StringField('WhatsApp Number', validators=[
        Optional(),
        Length(max=20, message='WhatsApp number must be less than 20 characters.')
    ])
    
    # Emergency Contact
    emergency_contact_name = StringField('Emergency Contact Name', validators=[
        Optional(),
        Length(max=100, message='Name must be less than 100 characters.')
    ])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[
        Optional(),
        Length(max=20, message='Phone number must be less than 20 characters.')
    ])
    emergency_contact_relationship = StringField('Relationship', validators=[
        Optional(),
        Length(max=50, message='Relationship must be less than 50 characters.')
    ])
    emergency_contact_address = TextAreaField('Emergency Contact Address', validators=[Optional()])
    
    # Professional Information
    occupation = StringField('Occupation', validators=[
        Optional(),
        Length(max=100, message='Occupation must be less than 100 characters.')
    ])
    company_name = StringField('Company Name', validators=[
        Optional(),
        Length(max=100, message='Company name must be less than 100 characters.')
    ])
    job_title = StringField('Job Title', validators=[
        Optional(),
        Length(max=100, message='Job title must be less than 100 characters.')
    ])
    work_address = TextAreaField('Work Address', validators=[Optional()])
    monthly_income = DecimalField('Monthly Income', validators=[
        Optional(),
        NumberRange(min=0, message='Income must be positive')
    ])
    
    # ID Information
    aadhar_number = StringField('Aadhar Number', validators=[
        Optional(),
        Length(max=20, message='Aadhar number must be less than 20 characters.')
    ])
    pan_number = StringField('PAN Number', validators=[
        Optional(),
        Length(max=20, message='PAN number must be less than 20 characters.')
    ])
    
    # Previous Address
    previous_address = TextAreaField('Previous Address', validators=[Optional()])
    previous_landlord_name = StringField('Previous Landlord Name', validators=[
        Optional(),
        Length(max=100, message='Name must be less than 100 characters.')
    ])
    previous_landlord_contact = StringField('Previous Landlord Contact', validators=[
        Optional(),
        Length(max=20, message='Contact must be less than 20 characters.')
    ])
    
    # Agreement Details
    lease_start_date = DateField('Lease Start Date', validators=[Optional()])
    lease_end_date = DateField('Lease End Date', validators=[Optional()])
    security_deposit = DecimalField('Security Deposit', validators=[
        Optional(),
        NumberRange(min=0, message='Security deposit must be positive')
    ])
    
    submit = SubmitField('Update Profile')
    
    def validate_new_password(self, field):
        """Custom validation for password fields"""
        # If any password field is filled, all must be filled
        if field.data or self.current_password.data or self.confirm_password.data:
            if not self.current_password.data:
                raise ValidationError('Current password is required to change password.')
            if not field.data:
                raise ValidationError('New password is required.')
            if not self.confirm_password.data:
                raise ValidationError('Password confirmation is required.')
    
    def validate_current_password(self, field):
        """Custom validation for current password"""
        # If any password field is filled, current password must be filled
        if self.new_password.data or self.confirm_password.data:
            if not field.data:
                raise ValidationError('Current password is required to change password.')

class DocumentUploadForm(FlaskForm):
    document_type = SelectField('Document Type', choices=[
        ('', 'Select Document Type'),
        ('aadhar', 'Aadhar Card'),
        ('pan', 'PAN Card'),
        ('agreement', 'Rental Agreement'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License'),
        ('bank_statement', 'Bank Statement'),
        ('salary_slip', 'Salary Slip'),
        ('other', 'Other Document')
    ], validators=[DataRequired(message='Please select a document type.')])
    
    file = FileField('Document File', validators=[
        FileRequired(message='Please select a file to upload.'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'], 
                   'Only images (JPG, PNG) and documents (PDF, DOC, DOCX) are allowed!')
    ])
    
    description = TextAreaField('Description (Optional)', validators=[Optional()])
    
    submit = SubmitField('Upload Document')

class DocumentVerificationForm(FlaskForm):
    verification_status = SelectField('Verification Status', choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    
    verification_notes = TextAreaField('Verification Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters.')
    ])
    
    submit = SubmitField('Update Verification Status')

class ProfilePictureForm(FlaskForm):
    profile_picture = FileField('Profile Picture', validators=[
        FileRequired(message='Please select a profile picture.'),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG, JPEG and PNG images are allowed!')
    ])
    
    submit = SubmitField('Upload Profile Picture')

class CreateRentPaymentForm(FlaskForm):
    renter_id = SelectField('Renter', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Rent Amount', validators=[
        DataRequired(),
        NumberRange(min=0, message='Amount must be positive')
    ])
    month = SelectField('Month', coerce=int, validators=[DataRequired()], choices=[
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ])
    year = IntegerField('Year', validators=[
        DataRequired(),
        NumberRange(min=2020, max=2030, message='Year must be between 2020 and 2030')
    ])
    due_date = DateField('Due Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Create Rent Payment Request')
