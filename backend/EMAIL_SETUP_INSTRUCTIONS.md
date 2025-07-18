# Gmail Email Setup Instructions

## Steps to Enable Real Email Sending

### 1. Enable 2-Step Verification

- Go to https://myaccount.google.com/security
- Sign in with ashraj77777@gmail.com
- Find "2-Step Verification" and enable it if not already enabled

### 2. Generate App Password

- Go to https://myaccount.google.com/apppasswords
- Select "Mail" as the app
- Select "Windows Computer" as the device
- Click "Generate"
- Copy the 16-character password (e.g., "abcd efgh ijkl mnop")

### 3. Update Configuration

Edit the `.env` file and update these lines:

```
MAIL_PASSWORD=your-16-character-app-password-here
MAIL_ENABLED=True
```

### 4. Restart Application

Restart your Flask application for changes to take effect.

## Current Status

- Email simulation mode is ACTIVE
- To enable real emails: Follow steps above
- Current sender: ashraj77777@gmail.com
- SMTP Server: smtp.gmail.com:587 (TLS)

## Testing

1. Try sending a test email to yourself first
2. Check spam folder if email doesn't arrive
3. Gmail may have initial sending limits for new app passwords

## Troubleshooting

- If you get "Less secure app" errors, use App Password instead
- Make sure 2-Step Verification is enabled first
- App passwords only work with 2-Step Verification enabled
- Gmail may block suspicious activity initially
