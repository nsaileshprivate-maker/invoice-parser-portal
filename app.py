import os
import re
import json
import secrets
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_file, session, redirect, url_for, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import pdfplumber
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import io
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Database
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/parser_db')

# Email Configuration (for OTP)
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
MAIL_FROM = os.environ.get('MAIL_FROM', MAIL_USERNAME)

# OTP Settings
OTP_EXPIRY_MINUTES = 10
OTP_LENGTH = 6

# Upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024
SESSION_TIMEOUT = 3600

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================================
# DATABASE CONNECTION POOL
# ============================================================================

db_pool = None

def get_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=DATABASE_URL
            )
            print("✓ Database connection pool created")
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            raise
    return db_pool

def get_db_connection():
    pool = get_db_pool()
    return pool.getconn()

def return_db_connection(conn):
    pool = get_db_pool()
    pool.putconn(conn)

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize PostgreSQL database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create users table with email_verified field
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create email_verifications table for OTP
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_verifications (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) NOT NULL,
                otp VARCHAR(6) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Create invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invoice_number TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                terms_of_payment TEXT,
                terms_of_delivery TEXT,
                currency TEXT,
                amount TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create shipments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shipments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ship_bill_no TEXT NOT NULL,
                ship_billing_date TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_submitted_at ON invoices(submitted_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_shipments_user_id ON shipments(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_shipments_submitted_at ON shipments(submitted_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_verifications_email ON email_verifications(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_verifications_otp ON email_verifications(otp)')
        
        conn.commit()
        print("✓ Database initialized successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Database initialization error: {e}")
        raise
    finally:
        cursor.close()
        return_db_connection(conn)

# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': 'Please login first', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT id, username, email, email_verified FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
            return user
        finally:
            cursor.close()
            return_db_connection(conn)
    return None

def get_user_id():
    return session.get('user_id')

# ============================================================================
# EMAIL HELPER FUNCTIONS
# ============================================================================

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))

def send_otp_email(email, otp, username):
    """Send OTP via email"""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print(f"⚠ Email not configured. OTP for {email}: {otp}")
        return True
    
    try:
        msg = MIMEMultipart()
        msg['From'] = MAIL_FROM
        msg['To'] = email
        msg['Subject'] = 'Verify Your Email - Invoice Parser Portal'

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 2px solid #1b5e20; padding-bottom: 20px; }}
                .header h1 {{ color: #1b5e20; margin: 0; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #1b5e20; text-align: center; padding: 20px; background: #e8f5e9; border-radius: 8px; margin: 20px 0; letter-spacing: 8px; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; }}
                .expiry {{ color: #666; font-size: 14px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 Invoice Parser Portal</h1>
                </div>
                <p>Hello <strong>{username}</strong>,</p>
                <p>Thank you for registering! Please verify your email address by entering the OTP below:</p>
                <div class="otp-code">{otp}</div>
                <p class="expiry">This OTP expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong></p>
                <p>If you didn't request this, please ignore this email.</p>
                <div class="footer">
                    <p>Invoice & Shipment Bill Parser Portal</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS:
            server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"✗ Email send error: {e}")
        return False# ============================================================================
# HELPER FUNCTIONS - PDF EXTRACTION
# ============================================================================

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_date_format(date_str):
    """Convert various date formats to DD-MM-YYYY format"""
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # Handle DD-MMM-YY format
    month_map = {
        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
    }
    
    # Try DD-MMM-YY format
    match = re.search(r'(\d{1,2})\s*[-/]?\s*([A-Z]{3})\s*[-/]?\s*(\d{2,4})', date_str, re.IGNORECASE)
    if match:
        day, month_str, year = match.groups()
        month_str_upper = month_str.upper()
        if month_str_upper in month_map:
            month = month_map[month_str_upper]
            year = int(year)
            if year < 100:
                year = 2000 + year if year < 50 else 1900 + year
            return f"{int(day):02d}-{month}-{year}"
    
    # Try DD.MM.YYYY or DD/MM/YYYY format
    match = re.search(r'(\d{1,2})\s*[./]\s*(\d{1,2})\s*[./]\s*(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{int(day):02d}-{int(month):02d}-{year}"
    
    # Try DD-MM-YYYY format
    match = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{int(day):02d}-{int(month):02d}-{year}"
    
    return date_str

def extract_invoice_data(pdf_path):
    """Extract invoice data from PDF using pdfplumber"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            result = {
                'invoiceNumber': '',
                'invoiceDate': '',
                'termsOfPayment': '',
                'termsOfDelivery': '',
                'currency': '',
                'amount': ''
            }
            
            # Extract Invoice Number
            patterns = [
                r'Invoice\s*No\s*&\s*Date\s*\n.*?(\d{10})',
                r'Invoice\s*No\s*&\s*Date\s*[^\d]*(\d+)',
                r'Invoice\s*No[.\s:]+(\d+)',
                r'INV[OICE]*\s*No[.\s:]+(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
                if match:
                    result['invoiceNumber'] = match.group(1).strip()
                    break
            
            # Extract Invoice Date
            patterns = [
                r'Invoice\s*(?:No\s*&\s*)?Date[.\s:]*([^\n]+?)(?:\n|$)',
                r'Dt:\s*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
                r'Date[.\s:]*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})'
            ]
            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    date_str = match.group(1).strip()
                    result['invoiceDate'] = convert_date_format(date_str)
                    break
            
            # Extract Terms of Payment
            pattern = r'Terms?\s*(?:of\s*)?Payment[.\s:]*([^\n]+?)(?:\n|$)'
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                result['termsOfPayment'] = match.group(1).strip()
            
            # Extract Terms of Delivery
            pattern = r'Terms?\s*(?:of\s*)?Delivery[.\s:]*([^\n]+?)(?:\n|$)'
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                result['termsOfDelivery'] = match.group(1).strip()
            
            # Extract Currency
            currency_pattern = r'(USD|EUR|INR|GBP|JPY|CHF|AUD|CAD|SGD|HKD)'
            match = re.search(currency_pattern, full_text)
            if match:
                result['currency'] = match.group(1)
            
            # Extract Amount
            patterns = [
                r'Grand\s*Total\s+(\d+\.?\d*)',
                r'Total\s*Amount[.\s:]*(\d+\.?\d*)',
                r'Total[.\s:]*(\d+\.?\d*)'
            ]
            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    result['amount'] = match.group(1)
                    break
            
            return result
    
    except Exception as e:
        return {'error': f'PDF parsing error: {str(e)}'}

def extract_shipment_data(pdf_path):
    """Extract shipping bill data from PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page_text = pdf.pages[0].extract_text()
            
            result = {
                'shipBillNo': '',
                'shipBillingDate': ''
            }
            
            # Get only the first 2000 characters (top section with SB info)
            top_section = first_page_text[:2000] if first_page_text else ""
            
            # Extract any 7-digit number (SB No is usually 7 digits)
            match = re.search(r'\b(\d{7})\b', top_section)
            if match:
                result['shipBillNo'] = match.group(1).strip()
            
            # Extract date in DD-MMM-YY format
            match = re.search(r'(\d{1,2})-([A-Z]{3})-(\d{2,4})', top_section, re.IGNORECASE)
            if match:
                day, month_str, year = match.groups()
                month_map = {
                    'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
                }
                month = month_map.get(month_str.upper(), '')
                year_int = int(year)
                if year_int < 100:
                    year_int = 2000 + year_int if year_int < 50 else 1900 + year_int
                result['shipBillingDate'] = f"{int(day):02d}-{month}-{year_int}"
            
            return result
    
    except Exception as e:
        return {'error': f'PDF parsing error: {str(e)}'}

# ============================================================================
# AUTHENTICATION ROUTES WITH EMAIL VERIFICATION
# ============================================================================

@app.route('/')
def index():
    """Serve the main HTML page if logged in, otherwise login page"""
    if 'user_id' in session:
        user = get_current_user()
        if user and user.get('email_verified', False):
            return send_file('index.html', mimetype='text/html')
        else:
            session.clear()
            return redirect('/login')
    return send_file('login.html', mimetype='text/html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return send_file('login.html', mimetype='text/html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect('/')
    return send_file('register.html', mimetype='text/html')

@app.route('/verify-otp')
def verify_otp_page():
    """Serve OTP verification page"""
    email = request.args.get('email')
    if not email:
        return redirect('/register')
    return send_file('verify_otp.html', mimetype='text/html')# ============================================================================
# AUTHENTICATION API ROUTES
# ============================================================================

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for verification"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        
        # Check if email is already registered and verified
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email_verified FROM users WHERE email = %s', (email,))
        existing = cursor.fetchone()
        
        if existing:
            if existing[1]:  # email_verified is True
                cursor.close()
                return_db_connection(conn)
                return jsonify({'status': 'error', 'message': 'Email already registered and verified'}), 400
            else:
                # User exists but not verified - we'll allow resending OTP
                pass
        
        cursor.close()
        return_db_connection(conn)
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Delete any existing unverified OTPs for this email
            cursor.execute('DELETE FROM email_verifications WHERE email = %s AND is_used = FALSE', (email,))
            
            # Insert new OTP
            expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            cursor.execute('''
                INSERT INTO email_verifications (email, otp, expires_at)
                VALUES (%s, %s, %s)
            ''', (email, otp, expires_at))
            
            conn.commit()
            
            # Send OTP via email
            username = data.get('username', 'User')
            send_otp_email(email, otp, username)
            
            return jsonify({
                'status': 'success',
                'message': f'OTP sent to {email}',
                'email': email
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            return_db_connection(conn)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and complete registration"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not email or not otp:
            return jsonify({'status': 'error', 'message': 'Email and OTP are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Verify OTP
            cursor.execute('''
                SELECT id, otp, created_at, expires_at, is_used
                FROM email_verifications
                WHERE email = %s AND otp = %s AND is_used = FALSE
                ORDER BY created_at DESC
                LIMIT 1
            ''', (email, otp))
            
            verification = cursor.fetchone()
            
            if not verification:
                return jsonify({'status': 'error', 'message': 'Invalid OTP'}), 400
            
            # Check if OTP expired
            if verification['expires_at'] < datetime.now():
                return jsonify({'status': 'error', 'message': 'OTP has expired. Please request a new one.'}), 400
            
            # Mark OTP as used
            cursor.execute('UPDATE email_verifications SET is_used = TRUE WHERE id = %s', (verification['id'],))
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user's verification status
                cursor.execute('''
                    UPDATE users 
                    SET email_verified = TRUE, username = %s, password_hash = %s
                    WHERE email = %s
                    RETURNING id
                ''', (username, generate_password_hash(password), email))
                
                user_id = cursor.fetchone()['id']
            else:
                # Create new user
                password_hash = generate_password_hash(password)
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, email_verified)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id
                ''', (username, email, password_hash))
                
                user_id = cursor.fetchone()['id']
            
            conn.commit()
            
            # Auto-login after verification
            session.permanent = True
            session['user_id'] = user_id
            session['username'] = username
            
            return jsonify({
                'status': 'success',
                'message': 'Email verified successfully!',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email
                }
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            return_db_connection(conn)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user - only if email is verified"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Username and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT id, username, email, password_hash, email_verified, is_active 
                FROM users 
                WHERE username = %s OR email = %s
            ''', (username, username))
            
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
            if not user['is_active']:
                return jsonify({'status': 'error', 'message': 'Account is disabled'}), 401
            
            # Check if email is verified
            if not user['email_verified']:
                return jsonify({
                    'status': 'error', 
                    'message': 'Please verify your email first. Check your inbox for OTP.',
                    'needs_verification': True,
                    'email': user['email']
                }), 401
            
            if not check_password_hash(user['password_hash'], password):
                return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
            # Update last login
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user['id'],))
            conn.commit()
            
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful!',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            return_db_connection(conn)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        
        # Generate new OTP
        otp = generate_otp()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Delete existing unverified OTPs
            cursor.execute('DELETE FROM email_verifications WHERE email = %s AND is_used = FALSE', (email,))
            
            # Insert new OTP
            expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            cursor.execute('''
                INSERT INTO email_verifications (email, otp, expires_at)
                VALUES (%s, %s, %s)
            ''', (email, otp, expires_at))
            
            conn.commit()
            
            # Send OTP
            send_otp_email(email, otp, 'User')
            
            return jsonify({
                'status': 'success',
                'message': 'OTP resent successfully'
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            return_db_connection(conn)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        user = get_current_user()
        if user and user.get('email_verified', False):
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })
        else:
            session.clear()
    return jsonify({'authenticated': False}), 401

@app.route('/api/current-user', methods=['GET'])
@login_required
def current_user():
    """Get current user info"""
    user = get_current_user()
    if user:
        return jsonify({
            'status': 'success',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    return jsonify({'status': 'error', 'message': 'User not found'}), 404# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.route('/extract-invoice', methods=['POST'])
@login_required
def extract_invoice():
    """Extract invoice data from uploaded PDF"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file. Only PDF allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{get_user_id()}_{filename}")
        file.save(filepath)
        
        extracted_data = extract_invoice_data(filepath)
        os.remove(filepath)
        
        if 'error' in extracted_data:
            return jsonify({'status': 'error', 'message': extracted_data['error']}), 400
        
        return jsonify({
            'status': 'success',
            'data': extracted_data
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/extract-invoice-bundle', methods=['POST'])
@login_required
def extract_invoice_bundle():
    """Extract invoice data from MULTIPLE uploaded PDFs"""
    if 'files' not in request.files:
        return jsonify({'status': 'error', 'message': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    
    if not files or len(files) == 0:
        return jsonify({'status': 'error', 'message': 'No files selected'}), 400
    
    try:
        all_extracted_data = []
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, f"{get_user_id()}_{filename}")
            file.save(filepath)
            
            extracted_data = extract_invoice_data(filepath)
            os.remove(filepath)
            
            if 'error' not in extracted_data:
                extracted_data['fileName'] = file.filename
                all_extracted_data.append(extracted_data)
        
        if len(all_extracted_data) == 0:
            return jsonify({'status': 'error', 'message': 'No valid PDF files found'}), 400
        
        return jsonify({
            'status': 'success',
            'data': all_extracted_data,
            'count': len(all_extracted_data)
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/submit-invoice', methods=['POST'])
@login_required
def submit_invoice():
    """Store submitted invoice data in database"""
    try:
        data = request.get_json()
        user_id = get_user_id()
        
        if not data.get('invoiceNumber') or not data.get('invoiceDate'):
            return jsonify({'status': 'error', 'message': 'Invoice Number and Date are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO invoices 
                (user_id, invoice_number, invoice_date, terms_of_payment, terms_of_delivery, currency, amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (
                user_id,
                data.get('invoiceNumber', ''),
                data.get('invoiceDate', ''),
                data.get('termsOfPayment', ''),
                data.get('termsOfDelivery', ''),
                data.get('currency', ''),
                data.get('amount', '')
            ))
            
            invoice_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Invoice submitted successfully',
                'id': invoice_id
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            return_db_connection(conn)
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-invoices', methods=['GET'])
@login_required
def get_invoices():
    """Get all submitted invoices for current user"""
    try:
        user_id = get_user_id()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT id, invoice_number, invoice_date, terms_of_payment, 
                   terms_of_delivery, currency, amount, submitted_at 
            FROM invoices 
            WHERE user_id = %s 
            ORDER BY submitted_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        return_db_connection(conn)
        
        invoices = []
        for row in rows:
            invoices.append({
                'id': row['id'],
                'invoiceNumber': row['invoice_number'],
                'invoiceDate': row['invoice_date'],
                'termsOfPayment': row['terms_of_payment'],
                'termsOfDelivery': row['terms_of_delivery'],
                'currency': row['currency'],
                'amount': row['amount'],
                'submittedAt': row['submitted_at']
            })
        
        return jsonify({'status': 'success', 'data': invoices})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# SHIPMENT ENDPOINTS
# ============================================================================

@app.route('/extract-shipment', methods=['POST'])
@login_required
def extract_shipment():
    """Extract shipment data from uploaded PDF"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file. Only PDF allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{get_user_id()}_{filename}")
        file.save(filepath)
        
        extracted_data = extract_shipment_data(filepath)
        os.remove(filepath)
        
        if 'error' in extracted_data:
            return jsonify({'status': 'error', 'message': extracted_data['error']}), 400
        
        return jsonify({
            'status': 'success',
            'data': extracted_data
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/extract-shipment-bundle', methods=['POST'])
@login_required
def extract_shipment_bundle():
    """Extract shipment data from MULTIPLE uploaded PDFs"""
    if 'files' not in request.files:
        return jsonify({'status': 'error', 'message': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    
    if not files or len(files) == 0:
        return jsonify({'status': 'error', 'message': 'No files selected'}), 400
    
    try:
        all_extracted_data = []
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, f"{get_user_id()}_{filename}")
            file.save(filepath)
            
            extracted_data = extract_shipment_data(filepath)
            os.remove(filepath)
            
            if 'error' not in extracted_data:
                extracted_data['fileName'] = file.filename
                all_extracted_data.append(extracted_data)
        
        if len(all_extracted_data) == 0:
            return jsonify({'status': 'error', 'message': 'No valid PDF files found'}), 400
        
        return jsonify({
            'status': 'success',
            'data': all_extracted_data,
            'count': len(all_extracted_data)
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/submit-shipment', methods=['POST'])
@login_required
def submit_shipment():
    """Store submitted shipment data in database"""
    try:
        data = request.get_json()
        user_id = get_user_id()
        
        if not data.get('shipBillNo') or not data.get('shipBillingDate'):
            return jsonify({'status': 'error', 'message': 'Ship Bill No and Date are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO shipments 
                (user_id, ship_bill_no, ship_billing_date)
                VALUES (%s, %s, %s) RETURNING id
            ''', (
                user_id,
                data.get('shipBillNo', ''),
                data.get('shipBillingDate', '')
            ))
            
            shipment_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Shipment submitted successfully',
                'id': shipment_id
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            return_db_connection(conn)
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-shipments', methods=['GET'])
@login_required
def get_shipments():
    """Get all submitted shipments for current user"""
    try:
        user_id = get_user_id()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT id, ship_bill_no, ship_billing_date, submitted_at 
            FROM shipments 
            WHERE user_id = %s 
            ORDER BY submitted_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        return_db_connection(conn)
        
        shipments = []
        for row in rows:
            shipments.append({
                'id': row['id'],
                'shipBillNo': row['ship_bill_no'],
                'shipBillingDate': row['ship_billing_date'],
                'submittedAt': row['submitted_at']
            })
        
        return jsonify({'status': 'success', 'data': shipments})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# EXPORT ENDPOINT
# ============================================================================

@app.route('/export-combined', methods=['GET'])
@login_required
def export_combined():
    """Export all invoices AND shipments to ONE Excel sheet with S.No"""
    try:
        user_id = get_user_id()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get invoices for current user
        cursor.execute('''
            SELECT invoice_number, invoice_date, terms_of_payment, 
                   terms_of_delivery, currency, amount 
            FROM invoices 
            WHERE user_id = %s 
            ORDER BY submitted_at DESC
        ''', (user_id,))
        invoice_rows = cursor.fetchall()
        
        # Get shipments for current user
        cursor.execute('''
            SELECT ship_bill_no, ship_billing_date 
            FROM shipments 
            WHERE user_id = %s 
            ORDER BY submitted_at DESC
        ''', (user_id,))
        shipment_rows = cursor.fetchall()
        
        cursor.close()
        return_db_connection(conn)
        
        # Create workbook with ONE sheet
        wb = Workbook()
        ws = wb.active
        ws.title = "All Data"
        
        current_row = 1
        
        # ===== INVOICES SECTION =====
        ws[f'A{current_row}'] = "INVOICES"
        ws[f'A{current_row}'].font = Font(bold=True, size=14, color="FFFFFF")
        ws[f'A{current_row}'].fill = PatternFill(start_color="1b5e20", end_color="1b5e20", fill_type="solid")
        current_row += 1
        
        # Invoice headers with S.No
        invoice_headers = ['S.No', 'Invoice Number', 'Invoice Date', 'Terms of Payment', 
                          'Terms of Delivery', 'Currency', 'Amount']
        for col, header in enumerate(invoice_headers, 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = header
            cell.fill = PatternFill(start_color="2e7d32", end_color="2e7d32", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1
        
        # Invoice data with S.No
        sno = 1
        for row in invoice_rows:
            ws.cell(row=current_row, column=1).value = sno
            ws.cell(row=current_row, column=2).value = row['invoice_number']
            ws.cell(row=current_row, column=3).value = row['invoice_date']
            ws.cell(row=current_row, column=4).value = row['terms_of_payment'] or ''
            ws.cell(row=current_row, column=5).value = row['terms_of_delivery'] or ''
            ws.cell(row=current_row, column=6).value = row['currency'] or ''
            ws.cell(row=current_row, column=7).value = row['amount'] or ''
            sno += 1
            current_row += 1
        
        # Blank row
        current_row += 2
        
        # ===== SHIPMENTS SECTION =====
        ws[f'A{current_row}'] = "SHIPMENTS"
        ws[f'A{current_row}'].font = Font(bold=True, size=14, color="FFFFFF")
        ws[f'A{current_row}'].fill = PatternFill(start_color="1b5e20", end_color="1b5e20", fill_type="solid")
        current_row += 1
        
        # Shipment headers with S.No
        shipment_headers = ['S.No', 'Ship Bill No', 'Ship Billing Date']
        for col, header in enumerate(shipment_headers, 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = header
            cell.fill = PatternFill(start_color="2e7d32", end_color="2e7d32", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1
        
        # Shipment data with S.No
        sno = 1
        for row in shipment_rows:
            ws.cell(row=current_row, column=1).value = sno
            ws.cell(row=current_row, column=2).value = row['ship_bill_no']
            ws.cell(row=current_row, column=3).value = row['ship_billing_date']
            sno += 1
            current_row += 1
        
        # Auto-size columns
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to bytes
        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        
        # Include username in filename
        user = get_current_user()
        username = user['username'] if user else 'user'
        
        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{username}_combined_data.xlsx'
        )
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ============================================================================
# USERNAME & EMAIL VALIDATION ROUTES
# ============================================================================

@app.route('/api/check-username', methods=['POST'])
def check_username():
    """Check if username is already taken"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'status': 'error', 'message': 'Username is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        existing = cursor.fetchone()
        
        cursor.close()
        return_db_connection(conn)
        
        if existing:
            return jsonify({'status': 'error', 'message': 'Username already taken'}), 409
        else:
            return jsonify({'status': 'success', 'message': 'Username available'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check-email', methods=['POST'])
def check_email():
    """Check if email is already registered"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, email_verified FROM users WHERE email = %s', (email,))
        existing = cursor.fetchone()
        
        cursor.close()
        return_db_connection(conn)
        
        if existing:
            if existing[1]:  # email_verified is True
                return jsonify({'status': 'error', 'message': 'Email already registered'}), 409
            else:
                return jsonify({'status': 'error', 'message': 'Email already registered but not verified. Please verify your email.'}), 409
        else:
            return jsonify({'status': 'success', 'message': 'Email available'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# FORGOT PASSWORD ROUTES
# ============================================================================

@app.route('/forgot-password')
def forgot_password_page():
    """Serve forgot password page"""
    return send_file('forgot_password.html', mimetype='text/html')

@app.route('/reset-password')
def reset_password_page():
    """Serve reset password page"""
    email = request.args.get('email')
    if not email:
        return redirect('/forgot-password')
    return send_file('reset_password.html', mimetype='text/html')

@app.route('/api/request-password-reset', methods=['POST'])
def request_password_reset():
    """Send OTP for password reset"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists with this email
        cursor.execute('SELECT id, username FROM users WHERE email = %s AND email_verified = TRUE', (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return_db_connection(conn)
            return jsonify({'status': 'error', 'message': 'No account found with this email'}), 404
        
        user_id = user[0]
        username = user[1]
        
        # Generate OTP
        otp = generate_otp()
        
        # Delete any existing unverified OTPs for this email
        cursor.execute('DELETE FROM email_verifications WHERE email = %s AND is_used = FALSE', (email,))
        
        # Insert new OTP
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        cursor.execute('''
            INSERT INTO email_verifications (email, otp, expires_at)
            VALUES (%s, %s, %s)
        ''', (email, otp, expires_at))
        
        conn.commit()
        cursor.close()
        return_db_connection(conn)
        
        # Send OTP via email with reset instructions
        send_password_reset_email(email, otp, username)
        
        return jsonify({
            'status': 'success',
            'message': 'Password reset OTP sent to your email',
            'email': email
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    """Verify OTP and reset password"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('newPassword', '')
        
        if not email or not otp or not new_password:
            return jsonify({'status': 'error', 'message': 'Email, OTP, and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify OTP
        cursor.execute('''
            SELECT id, created_at, expires_at, is_used
            FROM email_verifications
            WHERE email = %s AND otp = %s AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
        ''', (email, otp))
        
        verification = cursor.fetchone()
        
        if not verification:
            cursor.close()
            return_db_connection(conn)
            return jsonify({'status': 'error', 'message': 'Invalid OTP'}), 400
        
        # Check if OTP expired
        if verification[2] < datetime.now():
            cursor.close()
            return_db_connection(conn)
            return jsonify({'status': 'error', 'message': 'OTP has expired. Please request a new one.'}), 400
        
        # Mark OTP as used
        cursor.execute('UPDATE email_verifications SET is_used = TRUE WHERE id = %s', (verification[0],))
        
        # Update password
        password_hash = generate_password_hash(new_password)
        cursor.execute('UPDATE users SET password_hash = %s WHERE email = %s', (password_hash, email))
        
        conn.commit()
        cursor.close()
        return_db_connection(conn)
        
        return jsonify({
            'status': 'success',
            'message': 'Password reset successfully! Please login with your new password.'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_password_reset_email(email, otp, username):
    """Send password reset OTP via email"""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print(f"⚠ Email not configured. Password reset OTP for {email}: {otp}")
        return True
    
    try:
        msg = MIMEMultipart()
        msg['From'] = MAIL_FROM
        msg['To'] = email
        msg['Subject'] = 'Password Reset - Invoice Parser Portal'

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 2px solid #1b5e20; padding-bottom: 20px; }}
                .header h1 {{ color: #1b5e20; margin: 0; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #1b5e20; text-align: center; padding: 20px; background: #e8f5e9; border-radius: 8px; margin: 20px 0; letter-spacing: 8px; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; }}
                .expiry {{ color: #666; font-size: 14px; text-align: center; }}
                .warning {{ background: #fff3cd; padding: 12px; border-radius: 8px; margin: 16px 0; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Reset</h1>
                </div>
                <p>Hello <strong>{username}</strong>,</p>
                <p>We received a request to reset your password. Use the OTP below to set a new password:</p>
                <div class="otp-code">{otp}</div>
                <p class="expiry">This OTP expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong></p>
                <div class="warning">
                    ⚠️ If you didn't request this, please ignore this email and your password will remain unchanged.
                </div>
                <div class="footer">
                    <p>Invoice & Shipment Bill Parser Portal</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS:
            server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"✗ Email send error: {e}")
        return False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)