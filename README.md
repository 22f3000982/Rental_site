# Rental Management System

A comprehensive web-based rental management system built with Flask, designed to manage rent payments, electricity bills, meter readings, and tenant information.

## Features

### For Renters

- **Dashboard**: View current rent and electricity bill status
- **Payment Management**: Upload payment receipts and track payment history
- **Meter Readings**: View historical meter readings
- **Document Management**: Upload and manage personal documents
- **Export Features**: Download payment history in Excel/PDF format
- **Receipt Downloads**: Download individual receipts or bulk ZIP files
- **Profile Management**: Complete and manage personal profiles

### For Administrators

- **Tenant Management**: Approve/manage tenant accounts
- **Payment Verification**: Verify uploaded payment receipts
- **Meter Reading Management**: Add and track meter readings
- **Document Verification**: Verify tenant documents
- **Billing System**: Automatic electricity bill generation
- **Reports**: Monthly reports and payment history
- **System Settings**: Configure electricity rates and rent due dates

### Key Capabilities

- **Multi-format Exports**: Excel, PDF, and ZIP downloads
- **Payment Tracking**: Comprehensive payment history with filtering
- **Document Verification**: Admin approval system for tenant documents
- **Responsive Design**: Mobile-friendly Bootstrap interface
- **Secure File Uploads**: Receipt and document upload with validation
- **Profile Completion**: Track and encourage complete tenant profiles

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login
- **File Processing**: pandas, openpyxl for Excel exports
- **PDF Generation**: ReportLab for PDF reports
- **Forms**: WTForms for form handling and validation

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/22f3000982/Rental_site.git
   cd Rental_site
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Environment Configuration**

   ```bash
   # Copy the environment template
   cp .env.example .env

   # Edit .env file with your configurations
   # Set SECRET_KEY, DATABASE_URL, etc.
   ```

5. **Initialize Database**

   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
   ```

6. **Run the application**

   ```bash
   python app.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Default admin credentials will be created automatically

## Configuration

### Environment Variables

Create a `.env` file in the backend directory with:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///billing.db
FLASK_ENV=development
```

### Default Admin Account

- **Email**: ***********
- **Password**: *********
- **Username**: *********

## Usage

### For New Tenants

1. Register an account on the platform
2. Wait for admin approval
3. Complete your profile information
4. Upload required documents for verification
5. Start making payments and downloading receipts

### For Administrators

1. Login with admin credentials
2. Approve new tenant registrations
3. Add meter readings monthly
4. Verify payment receipts and documents
5. Generate reports and manage system settings

## File Structure

```
Rental_site/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── forms.py            # WTForms definitions
│   ├── requirements.txt    # Python dependencies
│   ├── templates/          # HTML templates
│   ├── static/            # CSS, JS, images
│   └── instance/          # Database files (not in git)
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── qr_code.jpeg          # QR code for payments
```

## API Endpoints

### Authentication

- `POST /register` - Register new tenant
- `POST /login` - User login
- `GET /logout` - User logout

### Tenant Routes

- `GET /renter/dashboard` - Tenant dashboard
- `GET /renter/payment_history_table` - Payment history with export
- `GET /download/payment_data` - Export payment data to Excel
- `GET /download/payment_receipts` - Download all receipts as ZIP
- `GET /download/payment_receipt/<id>/<type>` - Individual receipt download

### Admin Routes

- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/pending_payments` - Payment verification
- `POST /admin/verify_payment/<type>/<id>` - Verify payments
- `GET /admin/documents` - Document management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Security Features

- **File Upload Validation**: File type and size restrictions
- **Authentication Required**: All routes protected with login
- **Admin Authorization**: Separate admin and tenant permissions
- **Secure File Serving**: Controlled access to uploaded files
- **Input Validation**: Form validation with WTForms
- **CSRF Protection**: Built-in Flask-WTF CSRF protection

## Database Schema

The system uses SQLAlchemy ORM with the following main models:

- **User**: Tenant and admin accounts
- **RentPayment**: Monthly rent payment records
- **ElectricityBill**: Electricity consumption and billing
- **MeterReading**: Monthly meter readings
- **Document**: Tenant document uploads
- **Notification**: System notifications
- **UserProfile**: Extended tenant profiles

## Support

For support, please create an issue in the GitHub repository or contact the administrator.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 2.0

- Added comprehensive export functionality (Excel, PDF, ZIP)
- Implemented payment history table with filtering
- Added document verification system
- Enhanced profile management
- Improved mobile responsiveness
- Added bulk download features

### Version 1.0

- Initial release with basic rental management
- Payment tracking and receipt upload
- Admin verification system
- Basic reporting features
