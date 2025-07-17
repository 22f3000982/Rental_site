from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, DecimalField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional
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

class NotificationForm(FlaskForm):
    recipient_type = SelectField('Send To', choices=[
        ('all', 'All Active Renters'),
        ('individual', 'Individual Renter')
    ], validators=[DataRequired()], default='all')
    recipient_id = SelectField('Select Renter', coerce=int, validators=[Optional()])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=1, max=500, message='Message must be between 1 and 500 characters.')
    ], widget=TextArea())
    notification_type = SelectField('Type', choices=[
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('payment', 'Payment Related'),
        ('maintenance', 'Maintenance')
    ], validators=[DataRequired()])
    send_email = BooleanField('Send Email Notification', default=True)
    enable_chat = BooleanField('Enable Chat Response', default=False)
    submit = SubmitField('Send Notification')

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
    is_active = BooleanField('Active Status')
    is_approved = BooleanField('Approved Status')
    submit = SubmitField('Update Renter')
